"""Main entry point for the changelog_weaver package when run as a module."""

import asyncio
from .changelog import main as main_function


def run():
    """Run the main function of the package."""
    asyncio.run(main_function())


if __name__ == "__main__":
    run()
