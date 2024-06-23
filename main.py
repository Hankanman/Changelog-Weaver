"""Iterate and Print Work Items by Type"""

from __future__ import annotations
import asyncio
import logging as log
from typing import List
import aiohttp
from .src.config import Config
from .src.work_items import WorkItems, WorkItemChildren, WorkItem


def iterate_and_print(
    items_by_type: List[WorkItemChildren],
    config: Config,
    level: int = 1,
    icon_size: int = 20,
):
    """Recursively iterate through work items by type and print each level."""
    indent = "#" * level
    icon_size = icon_size - level if len(indent) > 1 else icon_size
    for item_group in items_by_type:
        print(f"{indent} Type: {item_group.type}")
        write_type_header(item_group, config, level, icon_size)
        for wi in item_group.items:
            print(f" - WorkItem ID: {wi.id}, Title: {wi.title}")
            if len(wi.children) > 0:
                write_parent_header(wi, config, level, icon_size)
            else:
                write_child_item(wi, config)
            if wi.children_by_type:
                iterate_and_print(wi.children_by_type, config, level + 1)


def write_type_header(wi: WorkItemChildren, config: Config, level: int, icon_size: int):
    """Generate and write the header for the parent item."""
    indent = "#" * level
    header = (
        f"{indent} "
        f"<img src='{wi.icon}' w='{icon_size}' h='{icon_size}'> "
        f"{wi.type}s\n\n"
    )
    config.output.write(header)


def write_parent_header(wi: WorkItem, config: Config, level: int, icon_size: int):
    """Generate and write the header for the parent item."""
    parent_head_link = f"[#{wi.id}]({wi.url}) " if wi.id != 0 else ""
    indent = "#" * level
    header = (
        f"{indent} "
        f"<img src='{wi.icon}' w='{icon_size}' h='{icon_size}' parent='{wi.parent}'>"
        f" {parent_head_link}{wi.title}\n\n"
    )
    config.output.write(header)


def write_child_item(wi: WorkItem, config: Config):
    """Write the child item to the markdown file."""
    config.output.write(
        f"- [#{wi.id}]({wi.url}) **{wi.title}** {wi.description} {wi.parent}\n"
    )


async def main():
    """Main function to fetch and iterate through work items by type."""
    config = Config()
    log.basicConfig(
        level=config.log_level,  # Set the logging level to INFO
        format="%(asctime)s - %(levelname)s - %(message)s",  # Format for the log messages
        handlers=[log.StreamHandler()],  # Output logs to the console
    )

    async with aiohttp.ClientSession() as session:
        wi = WorkItems()
        await wi.get_items(config, session)
        items_by_type = wi.by_type

        iterate_and_print(items_by_type, config)

    await config.close_session()
    input("Press Enter to exit...")


if __name__ == "__main__":
    asyncio.run(main())
