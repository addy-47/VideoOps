"""MoviePy/ImageIO frame extraction utility for visual QA inspection."""

import logging
from pathlib import Path
from moviepy import VideoFileClip

logger = logging.getLogger(__name__)


def extract_video_frames(
    video_path: Path, output_dir: Path, timestamps: list[float] | None = None
) -> list[Path]:
    """Extract JPEG frame images at specified timestamps from video file using MoviePy."""
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted_paths = []

    if not timestamps:
        timestamps = [5.0, 15.0, 25.0]

    try:
        clip = VideoFileClip(str(video_path))
        for i, ts in enumerate(timestamps):
            if ts < clip.duration:
                out_file = output_dir / f"frame_{i+1}_at_{ts:.1f}s.jpg"
                clip.save_frame(str(out_file), t=ts)
                if out_file.exists():
                    extracted_paths.append(out_file)
                    logger.info(f"Extracted frame at {ts:.1f}s -> {out_file}")
        clip.close()
    except Exception as e:
        logger.error(f"MoviePy frame extraction failed: {e}")

    return extracted_paths
