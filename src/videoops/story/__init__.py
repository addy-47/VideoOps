"""Story & Script Generation Engine (Layer 2)."""

from videoops.story.news_fetcher import get_latest_news
from videoops.story.script_generator import (
    generate_batch_image_prompts,
    generate_batch_video_queries,
    generate_comprehensive_content,
)

__all__ = [
    "get_latest_news",
    "generate_comprehensive_content",
    "generate_batch_video_queries",
    "generate_batch_image_prompts",
]
