"""Iterate and Print Work Items by Type"""

from __future__ import annotations
import asyncio
import logging as log
from typing import List
from .configuration import Config
from .work import Work
from .typings.types import HierarchicalWorkItem, WorkItemGroup
from .utilities.utils import create_contents


def iterate_and_print(
    items_by_type: List[WorkItemGroup],
    config: Config,
    level: int = 1,
    icon_size: int = 20,
):
    """Iterate through the work items by type and print them to the markdown file."""
    indent = "#" * level
    icon_size = icon_size - level if len(indent) > 1 else icon_size
    for item_group in items_by_type:
        write_type_header(item_group, config, level, icon_size)
        for wi in item_group.items:
            if isinstance(wi, HierarchicalWorkItem):
                if wi.type == "Other" and wi.children_by_type:
                    # Special handling for "Other" parent
                    iterate_and_print(wi.children_by_type, config, level + 1, icon_size)
                elif wi.children:
                    write_parent_header(wi, config, level + 1, icon_size)
                    if wi.children_by_type:
                        iterate_and_print(wi.children_by_type, config, level + 2)
                    else:
                        for child in wi.children:
                            write_child_item(child, config, level + 2, icon_size)
                else:
                    write_child_item(wi, config, level + 1, icon_size)
            else:
                log.warning("Unexpected item type: %s. Skipping.", type(wi))


def write_type_header(wi: WorkItemGroup, config: Config, level: int, icon_size: int):
    """Generate and write the header for the work item type group."""
    indent = "#" * (level + 1)
    header = (
        f"{indent} "
        f"<img src='{wi.icon}' height='{icon_size}' alt='{wi.type} Icon'> "
        f"{wi.type}{'s' if wi.type != 'Other' else ''}\n\n"
    )
    config.output.write(header)
    log.info("%s%s%s", " " * level, wi.type, "s" if wi.type != "Other" else "")


def write_parent_header(
    wi: HierarchicalWorkItem, config: Config, level: int, icon_size: int
):
    """Generate and write the header for the parent item.

    Args:
        wi (HierarchicalWorkItem): The hierarchical work item object.
        config (Config): The configuration object.
        level (int): The current level of the work item.
        icon_size (int): The size of the work item icon."""
    parent_head_link = f"[#{wi.id}]({wi.url}) " if wi.id != 0 else ""
    indent = "#" * (level + 1)
    header = (
        f"{indent} "
        f"<img src='{wi.icon}' height='{icon_size}' alt='{wi.type} Icon'>"
        f" {parent_head_link}{wi.title}\n\n"
    )
    config.output.write(header)
    log.info("%s%s%s | %s", level, " " * level, wi.id, wi.title)


def write_child_item(
    wi: HierarchicalWorkItem, config: Config, level: int, icon_size: int
):
    """Write the child item to the markdown file.

    Args:
        wi (HierarchicalWorkItem): The hierarchical work item object.
        config (Config): The configuration object.
        level (int): The current level of the work item."""
    config.output.write(
        f"- <img src='{wi.icon}' height='{icon_size}' alt='{wi.type} Icon'> [#{wi.id}]({wi.url}) **{wi.title}** {wi.summary}\n"
    )
    log.info("%s%s%s | %s", level, " " * (level + 1), wi.id, wi.title)


async def finalise_notes(config: Config) -> None:
    """
    Finalizes the release notes by adding the summary and table of contents.

    Args:
        html (bool): A boolean flag indicating whether to generate HTML output.
        summary_notes (str): The summary of the work items completed in this release.
        file_md (Path): The path to the output Markdown file.
        file_html (Path): The path to the output HTML file.
        section_headers (Array[str]): A Array of section headers for the table of contents.
    """
    log.info("Writing final summary and table of contents...")
    final_summary = await config.model.summarise(
        f"{config.prompts.summary}{config.project.brief}\n"
        f"The following is a summary of the work items completed in this release:\n"
        f"{config.project.changelog.notes}\nYour response should be as concise as possible",
    )

    config.output.set_summary(final_summary)
    config.output.set_toc(create_contents(config.project.changelog.headers))
    await config.output.finalize()
    log.info("Done!")


async def main():
    """Main function to fetch and iterate through work items by type."""
    config = Config()
    if not config.valid_env:
        input("Press Enter to exit...")
        return

    work = Work(config)
    await work.initialize()

    items_by_type = await work.generate_ordered_work_items()

    iterate_and_print(items_by_type, config)

    input("Press Enter to exit...")


if __name__ == "__main__":
    asyncio.run(main())
