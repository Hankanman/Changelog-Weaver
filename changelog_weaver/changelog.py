"""Iterate and Print Work Items by Type"""

from __future__ import annotations
import asyncio
import time
from typing import List, Union
from .configuration import Config
from .work import Work
from .typings import HierarchicalWorkItem, WorkItemGroup, WorkItem
from .logger import get_logger

log = get_logger(__name__)


def iterate_and_print(
    items_by_type: List[WorkItemGroup],
    config: Config,
    level: int = 1,
    icon_size: int = 20,
):
    """Iterate through the work items by type and print them to the markdown file."""
    indent = "#" * level
    icon_size = icon_size - level if len(indent) > 1 else icon_size
    i = 0
    for item_group in items_by_type:
        i += 1
        write_type_header(i, item_group, config, level, icon_size)
        for wi in item_group.items:
            handle_work_item(wi, config, level, icon_size)


def handle_work_item(
    wi: Union[HierarchicalWorkItem, WorkItem],
    config: Config,
    level: int,
    icon_size: int,
):
    """Handle the work item based on its type."""
    if isinstance(wi, HierarchicalWorkItem):
        handle_hierarchical_work_item(wi, config, level, icon_size)
    else:
        log.warning("Unexpected item type: %s. Skipping.", type(wi))


def handle_hierarchical_work_item(
    wi: HierarchicalWorkItem,
    config: Config,
    level: int,
    icon_size: int,
):
    """Handle the hierarchical work item."""
    if wi.type == "Other" and wi.children_by_type:
        # Special handling for "Other" parent
        iterate_and_print(wi.children_by_type, config, level + 1, icon_size)
    elif wi.children:
        write_parent_header(wi, config, level + 1, icon_size)
        if wi.children_by_type:
            iterate_and_print(wi.children_by_type, config, level + 2)
        else:
            for i, child in enumerate(wi.children):
                if i == len(wi.children) - 1:
                    write_child_item(child, config, icon_size, last_item=True)
                else:
                    write_child_item(child, config, icon_size)
    else:
        write_child_item(wi, config, icon_size, last_item=True)


def write_type_header(
    i: int, wi: WorkItemGroup, config: Config, level: int, icon_size: int
):
    """Generate and write the header for the work item type group."""
    indent = "#" * (level + 1)
    if i > 1 and level == 1:
        config.output.write("</div>\n\n")

    if level == 1:
        config.output.write(f"<a id='{wi.type.lower()}s'></a>\n\n")
    header = (
        f"{indent} "
        f"<img src='{wi.icon}' height='{icon_size}' alt='{wi.type} Icon'> "
        f"{wi.type}{'s' if wi.type != 'Other' else ''}\n\n"
    )
    config.output.write(header)
    if level == 1:
        config.output.write("<div style='margin-left:1em'>\n\n")


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


def write_child_item(
    wi: HierarchicalWorkItem,
    config: Config,
    icon_size: int,
    last_item=False,
):
    """Write the child item to the markdown file.

    Args:
        wi (HierarchicalWorkItem): The hierarchical work item object.
        config (Config): The configuration object.
        level (int): The current level of the work item."""
    config.output.write(
        f"- <img src='{wi.icon}' height='{icon_size}' alt='{wi.type} Icon'> [#{wi.id}]({wi.url}) **{wi.title}** {wi.summary}\n"
    )
    if last_item:
        config.output.write("\n")


async def finalise_notes(work: Work, config: Config) -> None:
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
    final_summary = await work.summarize_changelog(work.root_items)

    config.output.set_summary(final_summary)
    config.output.set_toc("v1.0.0", "Changelog Weaver", "2021-09-01")
    await config.output.finalize()
    log.info("Done!")


async def main():
    """Main function to generate the changelog."""

    log.info("Starting changelog generation process")
    overall_start_time = time.time()

    config = Config()
    if not config.valid_env:
        log.error("Invalid environment configuration")
        input("Press Enter to exit...")
        return

    work = Work(config)

    try:
        init_start_time = time.time()
        await work.initialize()
        init_end_time = time.time()
        log.info(
            "Work initialization completed in %.2f seconds",
            init_end_time - init_start_time,
        )

        log.info("Generating and printing ordered work items")
        items_start_time = time.time()
        iterate_and_print(await work.generate_ordered_work_items(), config)
        config.output.write("</div>\n")
        await finalise_notes(work, config)
        items_end_time = time.time()
        log.info(
            "Generated and printed ordered work items in %.2f seconds",
            items_end_time - items_start_time,
        )

        overall_end_time = time.time()
        log.info(
            "Total changelog generation time: %.2f seconds",
            overall_end_time - overall_start_time,
        )

    finally:
        await work.close()

    input("Press Enter to exit...")


if __name__ == "__main__":
    asyncio.run(main())
