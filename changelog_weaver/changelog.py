"""Module for generating changelogs."""

from __future__ import annotations
import asyncio
import time
import sys
from typing import List, Union
from .configuration import Config
from .work import Work
from .typings import HierarchicalWorkItem, WorkItemGroup, WorkItem, Platform
from .logger import get_logger

log = get_logger(__name__)

GITHUB_ICONS = {
    "Issues": "https://raw.githubusercontent.com/Hankanman/Changelog-Weaver/refs/heads/main/assets/issue-icon.svg",
    "Pull Requests": "https://raw.githubusercontent.com/Hankanman/Changelog-Weaver/refs/heads/main/assets/pull-request-icon.svg",
    "Commits": "https://raw.githubusercontent.com/Hankanman/Changelog-Weaver/refs/heads/main/assets/commit-icon.svg",
    "Comment": "https://raw.githubusercontent.com/Hankanman/Changelog-Weaver/refs/heads/main/assets/comment-icon.svg",
}

AZURE_ICONS = {
    "Epic": "https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_crown?color=E06C00&v=2",
    "Feature": "https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_trophy?color=773B93&v=2",
    "User Story": "https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_book?color=009CCC&v=2",
    "Bug": "https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_insect?color=CC293D&v=2",
    "Task": "https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_task?color=F2CB1D&v=2",
    "Other": "https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_review?color=333333&v=2",
}


def get_icon_html(icon_url: str, alt_text: str) -> str:
    """Generate HTML for an icon."""
    return f'<img src="{icon_url}" width="16" height="16" alt="{alt_text}" style="vertical-align: middle; margin-right: 5px;">'


def iterate_and_print(
    items_by_type: List[WorkItemGroup],
    config: Config,
):
    """Iterate through work items and print them in the changelog."""
    for item_group in items_by_type:
        write_type_header(item_group, config)
        if (
            item_group.type == "Commits"
            and config.project.platform.platform == Platform.GITHUB
        ):
            write_commit_items(item_group, config)
        else:
            for wi in item_group.items:
                handle_work_item(wi, config)
        config.output.write("</div>\n\n")  # Close the div for each group


def handle_work_item(
    wi: Union[HierarchicalWorkItem, WorkItem],
    config: Config,
):
    """Handle different types of work items."""
    if isinstance(wi, HierarchicalWorkItem):
        write_child_item(wi, config)
    else:
        log.warning("Unexpected item type: %s. Skipping.", type(wi))


def write_type_header(
    wi: WorkItemGroup,
    config: Config,
):
    """Write the header for a group of work items."""
    if config.project.platform.platform == Platform.GITHUB:
        icon_url = GITHUB_ICONS.get(wi.type, GITHUB_ICONS["Comment"])
    else:
        icon_url = AZURE_ICONS.get(wi.type, AZURE_ICONS["Other"])

    icon_html = get_icon_html(icon_url, f"{wi.type} Icon")

    config.output.write(f"<a id='{wi.type.lower().replace(' ', '-')}'></a>\n\n")
    header = f"## {icon_html} {wi.type}\n\n"
    config.output.write(header)
    config.output.write("<div style='margin-left:1em'>\n\n")


def write_commit_items(
    item_group: WorkItemGroup,
    config: Config,
):
    """Write commit items for GitHub."""
    for commit in item_group.items:
        if isinstance(commit, HierarchicalWorkItem) and hasattr(commit, "sha"):
            sha = commit.sha[:7] if commit.sha else ""
            title = commit.title if commit.title else ""
            url = commit.url if commit.url else "#"
            icon_html = get_icon_html(GITHUB_ICONS["Commits"], "Commit Icon")
            config.output.write(f"{icon_html} [{sha}]({url}) {title}\n")
    config.output.write("\n")


def write_child_item(
    wi: HierarchicalWorkItem,
    config: Config,
):
    """Write a child work item."""
    summary = wi.summary if wi.summary is not None else ""
    id_str = f"#{wi.id}" if wi.id is not None else ""
    title = wi.title if wi.title is not None else ""
    url = wi.url if wi.url is not None else "#"
    type_str = wi.type if wi.type is not None else "Unknown"

    if config.project.platform.platform == Platform.GITHUB:
        icon_url = GITHUB_ICONS.get(type_str, GITHUB_ICONS["Comment"])
    else:
        icon_url = AZURE_ICONS.get(type_str, AZURE_ICONS["Other"])

    icon_html = get_icon_html(icon_url, f"{type_str} Icon")

    config.output.write(f"{icon_html} [{id_str}]({url}) **{title}** {summary}\n")


async def finalise_notes(work: Work, config: Config) -> None:
    """Finalize the changelog by adding summary and table of contents."""
    log.info("Writing final summary and table of contents...")
    final_summary = await work.summarize_changelog(work.root_items)
    config.output.set_summary(final_summary)
    config.output.set_toc(
        config.project.version, config.project.name, time.strftime("%Y-%m-%d")
    )
    await config.output.finalize()
    log.info("Done!")


async def main():
    """Main function to generate the changelog."""
    log.info("Starting changelog generation process")
    overall_start_time = time.time()
    config = Config()
    if not config.valid_env:
        log.error("Invalid environment configuration")
        sys.exit(1)
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
        items_by_type = await work.generate_ordered_work_items()
        iterate_and_print(items_by_type, config)
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
    except Exception as e:
        log.error(
            f"An error occurred during changelog generation: {str(e)}", exc_info=True
        )
        raise
    finally:
        await work.close()
    log.info("Changelog generation completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
