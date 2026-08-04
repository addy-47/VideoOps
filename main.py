"""Main CLI entrypoint for videoops forwarding to vops CLI."""

import logging
import sys
from dotenv import load_dotenv

load_dotenv()

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

from videoops.cli.cli import main

if __name__ == "__main__":
    main()

