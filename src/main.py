""" Main script to write release notes based on Azure DevOps work items. """

from operator import le
import sys
import logging as log
from pathlib import Path
from typing import List
import asyncio
from .config import Config, ModelConfig
from .utils import setup_logs, finalise_notes
from .work_items import (
    Types,
    WorkItems,
    WorkItem,
    WorkItemChildren,
)


class OutputFile:
    """
    Represents an output file for the release notes.
    """

    _instance = None

    def __init__(self):
        if OutputFile._instance is not None:
            raise ValueError("This class is a singleton!")

        OutputFile._instance = self

        c = Config()
        folder_path = Path(".") / c.output_folder
        self.file = (
            folder_path / f"{c.solution_name}-v{c.release_version}.md"
        ).resolve()
        folder_path.mkdir(parents=True, exist_ok=True)

        self.setup_initial_content(c)

    def setup_initial_content(self, c):
        """Sets up the initial markdown content."""
        with open(self.file, "w", encoding="utf-8") as md_file:
            md_file.write(
                f"# Release Notes for {c.solution_name} version v{c.release_version}\n\n"
                f"## Summary\n\n"
                f"<NOTESSUMMARY>\n\n"
                f"## Quick Links\n\n"
                f"<TABLEOFCONTENTS>\n"
            )

    @classmethod
    def get_instance(cls):
        """Returns the singleton instance of the class."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def write(cls, content: str):
        """Appends content to the Markdown file."""
        instance = cls.get_instance()
        with open(instance.file, "a", encoding="utf-8") as file_output:
            file_output.write(content)


async def process_child_item(item: WorkItem) -> None:
    """Processes and writes a single child item to the file."""
    OutputFile.write(f"- [#{item.id}]({item.url}) **{item.title}**{item.description}\n")


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

        OutputFile.write(
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

        summary_notes += f"- {item.title}\n"
        parent_header = generate_header(item)

        if not item.children:
            log.info("No child items found for parent %s", item.id)
        else:
            OutputFile.write(parent_header)
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


async def write_notes(summarize_items: bool, output_html: bool):
    """
    Writes release notes based on the provided parameters.

    Args:
        summarize_items (bool): Flag indicating whether to summarize the work items.
        output_html (bool): Flag indicating whether to output the release notes in HTML format.
    """
    file_md = OutputFile.get_instance().file

    await Types().initialize()
    work_items = await WorkItems().initialize()
    ordered_work_items = work_items.group_by_type(work_items.items)

    summary_notes = await process_items(ordered_work_items)

    await finalise_notes(output_html, summary_notes, file_md)
    with open(file_md, "r", encoding="utf-8") as file:
        return file.read()


def main():
    """
    Entry point of the script.

    This function sets up the logs and checks if all the required environment variables are set.
    If any required variable is missing, it logs an error message and exits the script.
    Otherwise, it reads the content of the .env file and prints it.
    Finally, it runs the `write_notes` function with the specified parameters.
    """
    setup_logs()
    required_env_vars = [
        Config.solution_name,
        Config.release_version,
        Config.software_summary,
        Config.output_folder,
        ModelConfig.gpt_base_url,
        ModelConfig.model,
        ModelConfig.gpt_api_key,
    ]
    if any(not var for var in required_env_vars):
        log.error(
            "Please set the environment variables in the .env file before running the script."
        )
        sys.exit(1)
    else:
        with open(".env", "r", encoding="utf-8") as file:
            # Read the content of the file
            file_content = file.read()
            # Print the content
            print(file_content)
        result = asyncio.run(write_notes(True, True))
        return result


if __name__ == "__main__":
    main()
