"""Iterate and Print Work Items by Type"""

from __future__ import annotations
import asyncio
import logging as log
from typing import List
from src import Config, WorkItems, WorkItem, WorkItemChildren


def iterate_and_print(
    items_by_type: List[WorkItemChildren],
    config: Config,
    level: int = 1,
    icon_size: int = 20,
):
    """Iterate through the work items by type and print them to the markdown file.

    Args:
        items_by_type (List[WorkItemChildren]): The list of work items grouped by type.
        config (Config): The configuration object.
        level (int, optional): The current level of the work item. Default is 1.
        icon_size (int, optional): The size of the work item icon. Default is 20."""
    indent = "#" * level
    icon_size = icon_size - level if len(indent) > 1 else icon_size
    for item_group in items_by_type:
        write_type_header(item_group, config, level, icon_size)
        for wi in item_group.items:
            if len(wi.children) > 0:
                write_parent_header(wi, config, level + 1, icon_size)
            else:
                write_child_item(wi, config, level + 1)
            if wi.children_by_type:
                iterate_and_print(wi.children_by_type, config, level + 2)


def write_type_header(wi: WorkItemChildren, config: Config, level: int, icon_size: int):
    """Generate and write the header for the parent item.

    Args:
        wi (WorkItemChildren): The work item children object.
        config (Config): The configuration object.
        level (int): The current level of the work item.
        icon_size (int): The size of the work item icon."""
    indent = "#" * (level + 1)
    header = (
        f"{indent} " f"<img src='{wi.icon}' height='{icon_size}'> " f"{wi.type}s\n\n"
    )
    config.output.write(header)
    log.info("%s%ss", " " * level, wi.type)


def write_parent_header(wi: WorkItem, config: Config, level: int, icon_size: int):
    """Generate and write the header for the parent item.

    Args:
        wi (WorkItem): The work item object.
        config (Config): The configuration object.
        level (int): The current level of the work item.
        icon_size (int): The size of the work item icon."""
    parent_head_link = f"[#{wi.id}]({wi.url}) " if wi.id != 0 else ""
    indent = "#" * (level + 1)
    header = (
        f"{indent} "
        f"<img src='{wi.icon}' height='{icon_size}'>"
        f" {parent_head_link}{wi.title}\n\n"
    )
    config.output.write(header)
    log.info("%s%s | %s", " " * level, wi.id, wi.title)


def write_child_item(wi: WorkItem, config: Config, level: int):
    """Write the child item to the markdown file.

    Args:
        wi (WorkItem): The work item object.
        config (Config): The configuration object.
        level (int): The current level of the work item."""
    config.output.write(f"- [#{wi.id}]({wi.url}) **{wi.title}** {wi.summary}\n")
    log.info("%s%s | %s", " " * (level + 1), wi.id, wi.title)


async def main():
    """Main function to fetch and iterate through work items by type."""
    config = Config()
    if not config.valid_env:
        input("Press Enter to exit...")
        return

    await config.create_session()

    async with config.session:
        wi = WorkItems()
        await wi.get_items(config, False)
        items_by_type = wi.by_type

        iterate_and_print(items_by_type, config)

    await config.close_session()
    input("Press Enter to exit...")


if __name__ == "__main__":
    asyncio.run(main())
