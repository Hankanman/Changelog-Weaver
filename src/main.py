""" Main script to write release notes based on Azure DevOps work items. """

import sys
import logging as log
from typing import List
import aiohttp
from .config import Config
from .utils import setup_logs, finalise_notes
from .work_items import (
    Types,
    WorkItems,
    WorkItem,
    WorkItemChildren,
)


async def process_child_item(item: WorkItem) -> None:
    """Processes and writes a single child item to the file."""
    File.write(f"- [#{item.id}]({item.url}) **{item.title}**{item.description}\n")


async def update_group(
    grouped_children: List[WorkItemChildren],
) -> None:
    """
    Updates the release notes with details of grouped work items.

    Args:
        grouped_children (list of WorkItemChildren): The list of grouped child items.

    Returns:
        None
    """
    for group in grouped_children:
        log.info("Writing notes for %ss", group.type)

        File.write(
            f"### <img src='{group.icon}' alt='icon' width='12' height='12'> {group.type}s\n"
        )

        for child_item in group.items:
            await process_child_item(child_item)


async def process_items(work_items: List[WorkItemChildren]):
    """Processes work items and writes them to the markdown file."""
    summary_notes = ""
    for item in work_items:

        log.info(
            "Processing %s %s",
            len(item.items),
            f"{item.type}s" if len(item.items) > 1 else item.type,
        )

        summary_notes += f"- {item.type}\n"
        parent_header = generate_header(item)

        if not item.items:
            log.info("No child items found for parent %s", item.id)
        else:
            File.write(parent_header)
            await update_group(item.children)

    return summary_notes


def generate_header(item):
    """
    Generate a parent header for a given parent ID, link, icon URL, and title.

    Args:
        id (str): The ID of the parent.
        url (str): The link associated with the parent.
        icon (str): The URL of the icon for the parent.
        title (str): The title of the parent.

    Returns:
        str: The generated parent header.

    """
    parent_head_link = f"[#{item.id}]({item.url}) " if item.id != 0 else ""
    return (
        f"\n### <img src='{item.icon}' alt='icon' width='20' height='20'> "
        f"{parent_head_link}{item.title}\n"
    )


async def write_notes(config: Config, items: WorkItems, session: aiohttp.ClientSession):
    """Writes the release notes to a markdown file.
    Args:
        config (Config): The configuration object.
        items (WorkItems): The work items object.
        session (aiohttp.ClientSession): The aiohttp session object.
    Returns: None
    """

    for item in items.ordered_items:
        children = item.items
        await process_items(children)


async def main():
    """
    Entry point of the script.

    This function sets up the logs and checks if all the required environment variables are set.
    If any required variable is missing, it logs an error message and exits the script.
    Otherwise, it reads the content of the .env file and prints it.
    Finally, it runs the `write_notes` function with the specified parameters.
    """
    config = Config()
    session = config.session
    items = WorkItems(session)
    setup_logs()
    log.info("Starting release notes generation...")
    await write_notes(config, items, session)


if __name__ == "__main__":
    main()
