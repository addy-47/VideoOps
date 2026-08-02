"""MoviePy 2.2+ video compositor and timeline renderer with dynamic hardware resource management."""

import gc
import logging
import os
from pathlib import Path
from moviepy import AudioFileClip, ColorClip, CompositeVideoClip, ImageClip, VideoFileClip, vfx

from videoops.config import settings
from videoops.domain.models import Timeline
from videoops.media.text_overlay import TextOverlayBuilder

logger = logging.getLogger(__name__)


class VideoCompositor:
    """Composites visual assets, word-by-word caption overlays, and audio into final vertical video."""

    def __init__(self, temp_dir: Path | None = None) -> None:
        self.temp_dir = temp_dir or settings.resolved_temp_dir

    def render(self, timeline: Timeline, output_path: str, fps: int = 30) -> str:
        """Render composite timeline into vertical 1080x1920 MP4 file with dynamic CPU/RAM allocation."""
        logger.info(f"Starting rendering for timeline ({timeline.duration:.2f}s) to '{output_path}'")

        segment_clips = []
        all_child_clips = []
        current_time = 0.0

        crossfade_dur = 0.35  # Overlap crossfade duration in seconds
        current_time = 0.0

        for i, seg in enumerate(timeline.segments):
            is_last = (i == len(timeline.segments) - 1)
            clip_dur = seg.duration if is_last else seg.duration + crossfade_dur

            # 1. Background Visual Asset Clip (Image or Video)
            if seg.asset_path.endswith((".mp4", ".mov", ".webm", ".avi", ".mkv")):
                v_clip = VideoFileClip(seg.asset_path)
                if v_clip.duration < clip_dur:
                    v_clip = v_clip.looped(duration=clip_dur)
                else:
                    v_clip = v_clip.subclipped(0, clip_dur)
            else:
                v_clip = ImageClip(seg.asset_path).with_duration(clip_dur)

            # Resize/Crop to fill 1080x1920 base format before Ken Burns zoom
            v_clip = v_clip.resized(height=1920) if v_clip.h < 1920 else v_clip
            if v_clip.w < 1080:
                v_clip = v_clip.resized(width=1080)

            # Center crop to base 1080x1920
            crop_x1 = max(0, (v_clip.w - 1080) // 2)
            crop_y1 = max(0, (v_clip.h - 1920) // 2)
            v_clip = v_clip.cropped(x1=crop_x1, y1=crop_y1, width=1080, height=1920)

            # Alternating Ken Burns motion: Even cards zoom-in (1.0 -> 1.25), Odd cards zoom-out (1.25 -> 1.0)
            c_dur = max(0.1, clip_dur)
            if i % 2 == 0:
                v_clip = v_clip.resized(lambda t, dur=c_dur: 1.0 + 0.25 * (t / dur))
            else:
                v_clip = v_clip.resized(lambda t, dur=c_dur: 1.25 - 0.25 * (t / dur))

            v_clip = v_clip.cropped(x_center=v_clip.w / 2, y_center=v_clip.h / 2, width=1080, height=1920)

            # Apply CrossFadeIn transition for subsequent segments
            if i > 0:
                v_clip = v_clip.with_effects([vfx.CrossFadeIn(crossfade_dur)])

            v_clip = v_clip.with_start(0.0)
            all_child_clips.append(v_clip)

            # 2. Build animated word-by-word highlighted caption overlays for this segment
            card_text = seg.text or (timeline.title if i == 0 else "")
            words = card_text.split()
            word_overlay_clips = []

            if words:
                word_dur = seg.duration / len(words)
                import hashlib
                text_hash = hashlib.md5(card_text.encode("utf-8")).hexdigest()[:8]

                # Chunk text into 3-word sub-phrases for chronological glassmorphism badge animation
                chunk_size = 3
                word_chunks = [words[k:k + chunk_size] for k in range(0, len(words), chunk_size)]
                
                curr_word_time = 0.0
                total_words = len(words)

                for chunk_idx, chunk in enumerate(word_chunks):
                    chunk_text = " ".join(chunk)
                    for c_w_i in range(len(chunk)):
                        global_w_idx = (chunk_idx * chunk_size) + c_w_i
                        word_dur = seg.duration / total_words
                        
                        word_png_path = self.temp_dir / f"word_overlay_{i}_{global_w_idx}_{text_hash}.png"
                        TextOverlayBuilder.create_text_image(chunk_text, word_png_path, active_word_idx=c_w_i)

                        txt_clip = (
                            ImageClip(str(word_png_path))
                            .with_duration(word_dur)
                            .with_position(("center", "center"))
                            .with_effects([vfx.FadeIn(min(0.08, word_dur * 0.3))])
                            .with_start(curr_word_time)  # Relative to seg_clip start (0.0)
                        )
                        word_overlay_clips.append(txt_clip)
                        all_child_clips.append(txt_clip)
                        curr_word_time += word_dur

            # Solid background color layer to prevent any transparent black frames
            bg_solid = ColorClip(size=(1080, 1920), color=(15, 15, 25)).with_duration(clip_dur).with_start(0.0)
            all_child_clips.append(bg_solid)

            # Position segment clip at exact audio start time in master timeline
            seg_clip = CompositeVideoClip([bg_solid, v_clip] + word_overlay_clips, size=(1080, 1920)).with_duration(clip_dur).with_start(current_time)
            segment_clips.append(seg_clip)
            all_child_clips.append(seg_clip)

            current_time += seg.duration

        # Master composite video clip
        final_video = CompositeVideoClip(segment_clips, size=(1080, 1920)).with_duration(current_time)
        all_child_clips.append(final_video)
        all_child_clips.append(final_video)

        # Attach master audio track if present
        master_audio = None
        if timeline.audio_path and os.path.exists(timeline.audio_path):
            master_audio = AudioFileClip(timeline.audio_path)
            final_video = final_video.with_audio(master_audio)
            all_child_clips.append(master_audio)

        # Dynamic CPU and RAM Allocation via psutil
        import psutil
        available_ram_gb = psutil.virtual_memory().available / (1024 ** 3)
        logical_cores = os.cpu_count() or 2

        if available_ram_gb > 8.0:
            threads = max(1, logical_cores - 2)
            preset = "fast"
        elif available_ram_gb > 4.0:
            threads = max(1, min(4, logical_cores // 2))
            preset = "veryfast"
        else:
            threads = max(1, min(2, logical_cores // 4))
            preset = "ultrafast"

        logger.info(
            f"Dynamic Allocation ({available_ram_gb:.2f}GB RAM free) -> "
            f"allocated {threads} threads, preset={preset}"
        )

        # Render to disk with temp_audiofile explicitly confined to sandbox/temp/
        import hashlib
        audio_hash = hashlib.md5(output_path.encode("utf-8")).hexdigest()[:8]
        temp_audio_path = str(self.temp_dir / f"mpy_audio_{audio_hash}.m4a")

        final_video.write_videofile(
            output_path,
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            preset=preset,
            threads=threads,
            pixel_format="yuv420p",
            temp_audiofile=temp_audio_path,
            logger=None,
        )

        # Safely close all clips after rendering completes
        for clip in all_child_clips:
            try:
                clip.close()
            except Exception:
                pass

        # Force immediate garbage collection after rendering
        gc.collect()
        logger.info(f"Render completed successfully: {output_path}")
        return output_path
