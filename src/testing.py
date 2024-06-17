"""Iterate and Print Work Items by Type"""

from __future__ import annotations
import asyncio
import logging as log
from typing import List

from src.config import Config
from src.work_items import WorkItems, WorkItemChildren


async def main():
    """Main function to fetch and iterate through work items by type."""
    log.basicConfig(level=log.INFO)
    config = Config()
    session = config.session
    wi = WorkItems()
    await wi.get_items(config, session)
    items_by_type = wi.by_type

    iterate_and_print(items_by_type)
    await session.close()


def iterate_and_print(items_by_type: List[WorkItemChildren], level: int = 1):
    """Recursively iterate through work items by type and print each level."""
    indent = "#" * level
    for item_group in items_by_type:
        print(f"{indent} Type: {item_group.type}")
        for item in item_group.items:
            print(f" - WorkItem ID: {item.id}, Title: {item.title}")
            if item.children_by_type:
                iterate_and_print(item.children_by_type, level + 1)


if __name__ == "__main__":
    asyncio.run(main())
