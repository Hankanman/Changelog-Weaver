"""Module for generating changelogs."""

from __future__ import annotations
import asyncio
import time
import sys
from typing import List
from .configuration import Config
from .work import Work
from .typings import HierarchicalWorkItem, WorkItemGroup, Platform
from .logger import get_logger

log = get_logger(__name__)

GITHUB_ICONS = {
    "Issue": "https://raw.githubusercontent.com/Hankanman/Changelog-Weaver/refs/heads/main/assets/issue-icon.svg",
    "Pull Request": "https://raw.githubusercontent.com/Hankanman/Changelog-Weaver/refs/heads/main/assets/pull-request-icon.svg",
    "Commit": "https://raw.githubusercontent.com/Hankanman/Changelog-Weaver/refs/heads/main/assets/commit-icon.svg",
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


def get_icon_html(icon_url: str, alt_text: str, icon_size: int = 16) -> str:
    """Generate HTML for an icon."""
    return f'<img src="{icon_url}" width="{icon_size}" height="{icon_size}" alt="{alt_text}" style="vertical-align: middle; margin-right: 5px;">'


def iterate_and_print(
    items_by_type: List[WorkItemGroup],
    config: Config,
    level: int = 2,
):
    """
    Iterate through work items and print them in the changelog.

    Args:
        items_by_type (List[WorkItemGroup]): List of work item groups to process.
        config (Config): Configuration object.
        level (int): Header level for markdown formatting.
    """
    for item_group in items_by_type:
        write_type_header(item_group, config, level)
        if item_group.type == "Commit":
            write_commit_items(item_group, config)
        elif config.project.platform.platform == Platform.GITHUB:
            write_github_items(item_group, config)
        else:
            write_azure_devops_items(item_group, config, level + 1)
        config.output.write("</div>\n\n")


def write_github_items(item_group: WorkItemGroup, config: Config):
    """Write GitHub items to the changelog."""
    if item_group.type != "Commits":
        for wi in item_group.items:
            write_github_item(wi, config)


def write_azure_devops_items(item_group: WorkItemGroup, config: Config, level: int):
    """Write Azure DevOps items to the changelog."""
    for wi in item_group.items:
        write_azure_devops_item(wi, config, level)


def write_type_header(
    wi: WorkItemGroup,
    config: Config,
    level: int,
):
    """Write the header for a group of work items."""
    if config.project.platform.platform == Platform.GITHUB:
        icon_url = GITHUB_ICONS.get(wi.type, GITHUB_ICONS["Comment"])
    else:
        icon_url = AZURE_ICONS.get(wi.type, AZURE_ICONS["Other"])
    icon_html = get_icon_html(icon_url, f"{wi.type} Icon", 20)
    config.output.write(f"<a id='{wi.type.lower().replace(' ', '-')}s'></a>\n\n")
    header = f"{'#' * level} {icon_html} {wi.type}s\n\n"
    config.output.write(header)
    config.output.write("<div style='margin-left:1em'>\n\n")


def write_commit_items(
    item_group: WorkItemGroup,
    config: Config,
):
    """
    Write commit items.

    This function takes a group of commit items and writes them to the output
    in a formatted manner, including the commit hash, URL, and title.

    Args:
        item_group (WorkItemGroup): A group of commit items to be written.
        config (Config): The configuration object for the output.
    """
    log.info(f"Processing {len(item_group.items)} commits")
    for commit in item_group.items:
        log.debug(f"Processing commit: {commit}")
        if isinstance(commit, HierarchicalWorkItem) and hasattr(commit, "sha"):
            sha = commit.sha[:7] if commit.sha else "Unknown"
            title = commit.title if commit.title else ""
            url = commit.url if commit.url else "#"
            icon_html = get_icon_html(GITHUB_ICONS["Commit"], "Commit Icon")
            output_line = f"{icon_html} [{sha}]({url}) {title}\n"
            log.debug(f"Writing commit line: {output_line}")
            config.output.write(output_line)
        else:
            log.warning(f"Skipping invalid commit item: {commit}")
    config.output.write("\n")
    log.info("Finished processing commits")


def write_github_item(
    wi: HierarchicalWorkItem,
    config: Config,
):
    """Write a GitHub work item."""
    summary = wi.summary if wi.summary is not None else ""
    id_str = f"#{wi.id}" if wi.id is not None else ""
    title = wi.title if wi.title is not None else ""
    url = wi.url if wi.url is not None else "#"
    type_str = wi.type if wi.type is not None else "Unknown"
    icon_url = GITHUB_ICONS.get(type_str, GITHUB_ICONS["Comment"])
    icon_html = get_icon_html(icon_url, f"{type_str} Icon")
    config.output.write(f"{icon_html} [{id_str}]({url}) **{title}** {summary}\n")


def write_azure_devops_item(
    wi: HierarchicalWorkItem,
    config: Config,
    level: int,
):
    """Write an Azure DevOps work item."""
    type_str = wi.type if wi.type is not None else "Unknown"
    icon_url = AZURE_ICONS.get(type_str, AZURE_ICONS["Other"])
    icon_html = get_icon_html(icon_url, f"{type_str} Icon", 20 - level)
    id_str = f"#{wi.id}" if wi.id is not None else ""
    title = wi.title if wi.title is not None else ""
    url = wi.url if wi.url is not None else "#"
    summary = wi.summary if wi.summary is not None else ""

    header = f"{'#' * level} {icon_html} [{id_str}]({url}) {title}\n\n"
    config.output.write(header)

    if summary:
        config.output.write(f"{summary}\n\n")

    if wi.children:
        for child in wi.children:
            write_azure_devops_item(child, config, level + 1)


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
