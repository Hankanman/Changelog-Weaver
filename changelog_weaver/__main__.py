"""Main entry point for the changelog_weaver package when run as a module."""

import asyncio
import sys
from .changelog import main as main_function
from .logger import get_logger

log = get_logger(__name__)

# pylint: disable=broad-except
def run():
    """Run the main function of the package."""
    log.info("Starting Changelog Weaver")
    try:
        asyncio.run(main_function())
    except Exception as e:
        log.error(f"An error occurred: {str(e)}", exc_info=True)
        sys.exit(1)  # Exit with a non-zero status code to indicate an error


if __name__ == "__main__":
    run()
