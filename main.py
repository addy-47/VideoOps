"""Main CLI entrypoint for videoops AI YouTube Shorts generator."""

import logging
import sys
from dotenv import load_dotenv

# Load .env file before imports
load_dotenv()

from videoops.pipeline.orchestrator import ShortsPipelineOrchestrator

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("videoops")


def main() -> None:
    """CLI execution entrypoint."""
    mode = "auto"
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

    logger.info(f"Launching videoops pipeline in mode: {mode}")
    orchestrator = ShortsPipelineOrchestrator()
    video_path, thumbnail_path = orchestrator.run(mode=mode)

    print("\n" + "=" * 50)
    print("SUCCESSFULLY GENERATED YOUTUBE SHORT!")
    print(f"Video File: {video_path}")
    print(f"Thumbnail:  {thumbnail_path}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
