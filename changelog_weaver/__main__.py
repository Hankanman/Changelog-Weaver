"""Main entry point for the changelog_weaver package when run as a module."""

import asyncio
from .changelog import main as main_function
from .logger import get_logger

log = get_logger(__name__)


def run():
    """Run the main function of the package."""
    log.info("Starting Changelog Weaver")
    asyncio.run(main_function())


if __name__ == "__main__":
    run()
