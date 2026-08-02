"""Pipeline Orchestrator with parallel asset acquisition and clean domain timeline management."""

import concurrent.futures
from datetime import datetime
import logging
import uuid
from pathlib import Path
from videoops.assets.audio import TTSProvider
from videoops.assets.thumbnail import ThumbnailGenerator
from videoops.assets.visual import VisualAssetProvider
from videoops.config import settings
from videoops.domain.models import AssetType, ClipSegment, Timeline
from videoops.media.compositor import VideoCompositor
from videoops.publishing.youtube import YouTubePublisher
from videoops.story.news_fetcher import get_latest_news
from videoops.story.script_generator import (
    generate_batch_image_prompts,
    generate_batch_video_queries,
    generate_comprehensive_content,
)

logger = logging.getLogger(__name__)


class ShortsPipelineOrchestrator:
    """Orchestrates pipeline execution from news headline to YouTube upload."""

    def _purge_old_temp_sandbox(self) -> None:
        """Purge stale temp run directories from sandbox/temp/ before new pipeline execution."""
        temp_dir = settings.resolved_temp_dir
        if not temp_dir.exists():
            return
        import shutil
        import time
        now = time.time()
        for item in temp_dir.iterdir():
            if item.is_dir() and item.name.startswith("run_"):
                # Purge temp directories older than 30 minutes
                if (now - item.stat().st_mtime) > 1800:
                    try:
                        shutil.rmtree(item)
                        logger.info(f"Purged stale temp sandbox run directory: {item.name}")
                    except Exception as e:
                        logger.warning(f"Could not purge stale temp directory {item}: {e}")

    def run(self, topic: str | None = None, mode: str = "auto") -> tuple[str, str]:
        """Execute full end-to-end pipeline run with parallel asset acquisition."""
        self._purge_old_temp_sandbox()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        work_dir = settings.resolved_temp_dir / f"run_{timestamp}_{uuid.uuid4().hex[:8]}"
        work_dir.mkdir(parents=True, exist_ok=True)

        # Layer 2: Story Generation Engine
        logger.info("[Step 1/4] Generating script content with LLM...")
        if not topic:
            headline = get_latest_news()
            topic = headline or "Latest Breaking Tech & AI Discoveries"

        logger.info(f"=== STARTING VIDEOOPS PIPELINE FOR TOPIC: '{topic}' ===")

        content_pkg = generate_comprehensive_content(topic)

        # Layer 3: Asset Acquisition Engine (PARALLEL EXECUTION)
        logger.info("[Step 2/4] Synthesizing TTS audio and fetching visual assets in parallel...")
        tts_provider = TTSProvider(output_dir=work_dir)
        visual_provider = VisualAssetProvider(output_dir=work_dir)

        card_texts = [card.text for card in content_pkg.script_cards]

        # Resolve video/image mode
        if mode == "auto":
            day_of_year = datetime.now().timetuple().tm_yday
            use_video = (day_of_year % 2 != 0)
        else:
            use_video = (mode == "video")

        if use_video:
            queries = generate_batch_video_queries(card_texts, topic)
        else:
            queries = generate_batch_image_prompts(card_texts, topic)

        # 1. Parallel TTS Synthesis
        def _fetch_card_audio(idx_card):
            idx, card = idx_card
            audio_asset = tts_provider.synthesize(card.text, filename_prefix=f"sec_{idx}")
            return idx, audio_asset

        # 2. Parallel Visual Asset Fetching (Prioritize Stock Video)
        def _fetch_card_visual(idx_card_query):
            idx, card, query = idx_card_query
            v_asset = visual_provider.fetch_video(query, min_duration=card.duration or 5.0)
            if not v_asset or v_asset.asset_type != AssetType.VIDEO:
                v_asset = visual_provider.fetch_image(query)
            return idx, v_asset

        num_cards = len(content_pkg.script_cards)
        audio_results = [None] * num_cards
        visual_results = [None] * num_cards

        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, num_cards * 2)) as executor:
            # Submit TTS tasks
            tts_futures = [
                executor.submit(_fetch_card_audio, (i, card))
                for i, card in enumerate(content_pkg.script_cards)
            ]
            # Submit Visual tasks with explicit topic-focused background queries
            visual_futures = [
                executor.submit(_fetch_card_visual, (i, card, card.background_query or queries.get(i) or topic))
                for i, card in enumerate(content_pkg.script_cards)
            ]

            # Wait for all asset acquisitions to complete safely
            for future in concurrent.futures.as_completed(tts_futures):
                try:
                    idx, audio_asset = future.result()
                    audio_results[idx] = audio_asset
                except Exception as e:
                    logger.error(f"TTS asset acquisition failed for task: {e}")

            for future in concurrent.futures.as_completed(visual_futures):
                try:
                    idx, v_asset = future.result()
                    visual_results[idx] = v_asset
                except Exception as e:
                    logger.error(f"Visual asset acquisition failed for task: {e}")

        # Build segments list in perfect 1-to-1 audio/video sync order
        segments = []
        audio_paths = []
        total_duration = 0.0

        for i, card in enumerate(content_pkg.script_cards):
            audio_asset = audio_results[i]
            v_asset = visual_results[i]

            # Fallback if any asset failed
            if audio_asset is None:
                logger.warning(f"Audio asset missing for card {i}. Synthesizing fallback...")
                audio_asset = tts_provider.synthesize(card.text, filename_prefix=f"fallback_audio_{i}")

            if v_asset is None:
                logger.warning(f"Visual asset missing for card {i}. Fetching fallback image...")
                v_asset = visual_provider.fetch_video(card.background_query or topic, min_duration=card.duration)

            audio_paths.append(audio_asset.path)

            seg = ClipSegment(
                asset_path=v_asset.path,
                start_time=total_duration,
                duration=audio_asset.duration,
                text=card.text,
                crossfade_in=0.35 if i > 0 else 0.0,
            )
            segments.append(seg)
            total_duration += audio_asset.duration

        # Merge audio tracks into single master audio track
        master_audio_path = work_dir / "master_audio.mp3"
        self._concat_audio_files(audio_paths, master_audio_path)

        # Generate Thumbnail
        logger.info("Generating video thumbnail...")
        thumbnail_gen = ThumbnailGenerator()
        thumbnail_path = thumbnail_gen.generate(
            title=content_pkg.title,
            prompt=content_pkg.thumbnail_hf_prompt or content_pkg.thumbnail_unsplash_query,
        )

        # Layer 4: Media Composition Engine
        logger.info("[Step 3/4] Compositing video timeline and rendering...")
        timeline = Timeline(
            duration=total_duration,
            segments=tuple(segments),
            audio_path=str(master_audio_path),
            title=content_pkg.title,
        )

        safe_title = "".join(c for c in content_pkg.title if c.isalnum() or c in (" ", "_")).replace(" ", "_")[:30]
        output_filename = settings.resolved_output_dir / f"yt_short_{safe_title}_{timestamp}.mp4"

        compositor = VideoCompositor(temp_dir=work_dir)
        video_path = compositor.render(timeline, str(output_filename))

        # Extract video frames for visual QA inspection across Word 0 -> Word 1 -> Word 2 chronological progression
        from videoops.media.frame_extractor import extract_video_frames
        sample_times = [0.08, 0.25, 0.50, 0.75, 0.92]
        frame_dir = settings.resolved_temp_dir / f"frame_samples_{timestamp}"
        extracted_frames = extract_video_frames(Path(video_path), frame_dir, sample_times)
        logger.info(f"Extracted {len(extracted_frames)} sample frames for visual QA in {frame_dir}")

        # Layer 5: Publishing
        logger.info("[Step 4/4] Publishing video...")
        publisher = YouTubePublisher()
        publisher.publish(
            video_path=video_path,
            title=content_pkg.title,
            description=content_pkg.description,
            thumbnail_path=thumbnail_path,
        )

        logger.info("=== PIPELINE EXECUTION COMPLETED SUCCESSFULLY ===")
        return video_path, thumbnail_path

    def _concat_audio_files(self, audio_paths: list[str], output_path: Path) -> Path:
        """Concatenate individual TTS audio section files into master audio file."""
        from moviepy import AudioFileClip, concatenate_audioclips
        from contextlib import ExitStack

        with ExitStack() as stack:
            clips = [stack.enter_context(AudioFileClip(p)) for p in audio_paths]
            final_audio = concatenate_audioclips(clips)
            final_audio.write_audiofile(str(output_path), logger=None)

        return output_path
