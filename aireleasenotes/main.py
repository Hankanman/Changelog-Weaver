""" Main script to write release notes based on Azure DevOps work items. """

import base64
import sys
import logging as log
from pathlib import Path
from urllib.parse import quote
from collections import defaultdict
import asyncio
import aiohttp
from .config import (
    ORG_NAME,
    PROJECT_NAME,
    SOLUTION_NAME,
    RELEASE_VERSION,
    RELEASE_QUERY,
    PAT,
    GPT_API_KEY,
    MODEL,
    MODEL_BASE_URL,
    DEVOPS_BASE_URL,
    DESIRED_WORK_ITEM_TYPES,
    OUTPUT_FOLDER,
    SOFTWARE_SUMMARY,
    DEVOPS_API_VERSION,
)
from .enums import WorkItemField, APIEndpoint
from .utils import (
    setup_logs,
    clean_string,
    get_icons,
    get_items,
    update_group,
    finalise_notes,
    GroupUpdateConfig,
)


class ProcessConfig:
    """
    Represents a configuration for processing data.

    Args:
        session (str): The session information.
        file_md (str): The file metadata.
        summarize_items (bool): Flag indicating whether to summarize items.
        work_item_type_to_icon (dict): A dictionary mapping work item types to icons.
    """

    def __init__(self, session, file_md, summarize_items, work_item_type_to_icon):
        self.session = session
        self.file_md = file_md
        self.summarize_items = summarize_items
        self.work_item_type_to_icon = work_item_type_to_icon

    def get_summary_flag(self):
        """Returns the summarize_items flag."""
        return self.summarize_items

    def set_summary_flag(self, summarize_items):
        """Sets the summarize_items flag."""
        self.summarize_items = summarize_items

    def add_work_item_type_icon(self, work_item_type, icon_url):
        """Adds a new work item type to icon mapping."""
        self.work_item_type_to_icon[work_item_type] = icon_url

    def get_icon_url(self, work_item_type):
        """Gets the icon URL for a given work item type."""
        return self.work_item_type_to_icon.get(work_item_type)

    def get_file_md_path(self):
        """Returns the file path for the markdown file."""
        return self.file_md


def setup_files():
    """Sets up the necessary file paths and initial markdown content."""
    folder_path = Path(".") / OUTPUT_FOLDER
    file_md = (folder_path / f"{SOLUTION_NAME}-v{RELEASE_VERSION}.md").resolve()
    file_html = (folder_path / f"{SOLUTION_NAME}-v{RELEASE_VERSION}.html").resolve()
    folder_path.mkdir(parents=True, exist_ok=True)

    with open(file_md, "w", encoding="utf-8") as md_file:
        md_file.write(
            f"# Release Notes for {SOLUTION_NAME} version v{RELEASE_VERSION}\n\n"
            f"## Summary\n\n"
            f"<NOTESSUMMARY>\n\n"
            f"## Quick Links\n\n"
            f"<TABLEOFCONTENTS>\n"
        )

    return file_md, file_html


def encode_pat():
    """Encodes the PAT for authorization."""
    return base64.b64encode(f":{PAT}".encode()).decode()


async def fetch_parent_items(
    session, org_name_escaped, project_name_escaped, parent_ids
):
    """Fetches parent work items from Azure DevOps."""
    parent_work_items = {}
    for parent_id in parent_ids:
        parent_uri = DEVOPS_BASE_URL + APIEndpoint.WORK_ITEM.value.format(
            org_name=org_name_escaped,
            project_name=project_name_escaped,
            parent_id=parent_id,
        )
        if parent_id != "0":
            async with session.get(parent_uri) as parent_response:
                parent_work_items[parent_id] = await parent_response.json()
    return parent_work_items


def group_items(work_items):
    """Groups work items by their parent."""
    parent_child_groups = defaultdict(list)
    for item in work_items:
        parent_link = next(
            (
                rel
                for rel in item.get("relations", [])
                if rel["rel"] == "System.LinkTypes.Hierarchy-Reverse"
            ),
            None,
        )
        if parent_link:
            parent_id = parent_link["url"].split("/")[-1]
            parent_child_groups[parent_id].append(item)
        else:
            log.info("Work item %s has no parent", item["id"])
            item["fields"][WorkItemField.PARENT.value] = 0
            parent_child_groups["0"].append(item)
    return parent_child_groups


def add_other_parent(parent_work_items):
    """Adds a placeholder for items with no parent."""
    parent_work_items["0"] = {
        "id": 0,
        "fields": {
            WorkItemField.TITLE.value: "Other",
            WorkItemField.WORK_ITEM_TYPE.value: "Other",
            WorkItemField.PARENT.value: 0,
        },
        "_links": {
            "html": {"href": "#"},
            "workItemIcon": {
                "url": "https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_clipboard_issue?color=577275&v=2"
            },
        },
        "url": "#",
    }


async def process_items(config, work_items, parent_work_items):
    """Processes work items and writes them to the markdown file."""
    summary_notes = ""
    for work_item_type in DESIRED_WORK_ITEM_TYPES:
        log.info("Processing %ss", work_item_type)
        parent_ids_of_type = get_parent_ids_by_type(parent_work_items, work_item_type)

        for parent_id in parent_ids_of_type:
            parent_work_item = parent_work_items[parent_id]
            parent_title = clean_string(
                parent_work_item["fields"][WorkItemField.TITLE.value]
            )
            log.info("%s | %s | %s", work_item_type, parent_id, parent_title)

            parent_link, parent_icon_url = get_parent_link_icon(
                parent_work_item, config.work_item_type_to_icon, work_item_type
            )
            child_items = get_child_items(work_items, parent_id)

            if not child_items:
                log.info("No child items found for parent %s", parent_id)

            summary_notes += f"- {parent_title}\n"
            parent_header = generate_header(
                parent_id, parent_link, parent_icon_url, parent_title
            )

            grouped_child_items = group_items_by_type(child_items)
            if grouped_child_items:
                write_header(config.file_md, parent_header)
                await update_group(
                    GroupUpdateConfig(
                        summary_notes,
                        grouped_child_items,
                        config.work_item_type_to_icon,
                        config.file_md,
                        config.session,
                        config.summarize_items,
                    )
                )

    return summary_notes


def get_parent_ids_by_type(parent_work_items, work_item_type):
    """
    Returns a list of parent work item IDs that match the specified work item type.

    Args:
        parent_work_items (dict): A dictionary containing parent work items, where the keys are the work item IDs and the values are the work item details.
        work_item_type (str): The work item type to filter by.

    Returns:
        list: A list of parent work item IDs that match the specified work item type.
    """
    return [
        pid
        for pid, item in parent_work_items.items()
        if item["fields"]["System.WorkItemType"] == work_item_type
    ]


def get_parent_link_icon(parent_work_item, work_item_type_to_icon, work_item_type):
    """
    Get the parent link and icon URL for a given work item.

    Args:
        parent_work_item (dict): The parent work item.
        work_item_type_to_icon (dict): A dictionary mapping work item types to their corresponding icon URLs.
        work_item_type (str): The type of the work item.

    Returns:
        tuple: A tuple containing the parent link and icon URL.
    """
    parent_link = parent_work_item["_links"]["html"]["href"]
    parent_icon_url = work_item_type_to_icon.get(work_item_type)["iconUrl"]
    return parent_link, parent_icon_url


def get_child_items(work_items, parent_id):
    """
    Returns a list of child work items based on the given parent ID.

    Parameters:
    work_items (list): A list of work items.
    parent_id (int): The ID of the parent work item.

    Returns:
    list: A list of child work items.
    """
    return [
        wi
        for wi in work_items
        if wi["fields"].get(WorkItemField.PARENT.value) == int(parent_id)
    ]


def generate_header(parent_id, parent_link, parent_icon_url, parent_title):
    """
    Generate a parent header for a given parent ID, link, icon URL, and title.

    Args:
        parent_id (str): The ID of the parent.
        parent_link (str): The link associated with the parent.
        parent_icon_url (str): The URL of the icon for the parent.
        parent_title (str): The title of the parent.

    Returns:
        str: The generated parent header.

    """
    parent_head_link = f"[#{parent_id}]({parent_link}) " if parent_id != "0" else ""
    return (
        f"\n### <img src='{parent_icon_url}' alt='icon' width='20' height='20'> "
        f"{parent_head_link}{parent_title}\n"
    )


def group_items_by_type(child_items):
    """
    Groups child items by their work item type.

    Parameters:
    - child_items (list): A list of child items.

    Returns:
    - grouped_child_items (defaultdict): A defaultdict containing the child items grouped by their work item type.
    """
    grouped_child_items = defaultdict(list)
    for item in child_items:
        grouped_child_items[item["fields"][WorkItemField.WORK_ITEM_TYPE.value]].append(
            item
        )
    return grouped_child_items


def write_header(file_md, parent_header):
    """
    Appends the parent header to the specified Markdown file.

    Args:
        file_md (str): The path to the Markdown file.
        parent_header (str): The parent header to be written.

    Returns:
        None
    """
    with open(file_md, "a", encoding="utf-8") as file_output:
        file_output.write(parent_header)


async def write_notes(
    query_id: str, section_header: str, summarize_items: bool, output_html: bool
):
    """
    Writes release notes based on the provided parameters.

    Args:
        query_id (str): The ID of the query to fetch work items from.
        section_header (str): The header for the release notes section.
        summarize_items (bool): Flag indicating whether to summarize the work items.
        output_html (bool): Flag indicating whether to output the release notes in HTML format.
    """
    org_name_escaped, project_name_escaped, devops_headers = setup_environment()
    file_md, file_html = setup_files()

    async with aiohttp.ClientSession(headers=devops_headers) as session:
        config = ProcessConfig(
            session,
            file_md,
            summarize_items,
            await get_icons(session, ORG_NAME, PROJECT_NAME),
        )
        parent_work_items = await fetch_parent_items(
            session,
            org_name_escaped,
            project_name_escaped,
            group_items(
                await get_items(session, ORG_NAME, PROJECT_NAME, query_id)
            ).keys(),
        )
        add_other_parent(parent_work_items)

        summary_notes = await process_items(
            config,
            await get_items(session, ORG_NAME, PROJECT_NAME, query_id),
            parent_work_items,
        )

        await finalise_notes(
            output_html, summary_notes, file_md, file_html, [section_header]
        )
        with open(file_md, "r", encoding="utf-8") as file:
            return file.read()


def setup_environment():
    """Setup environment variables and headers."""
    org_name_escaped = quote(ORG_NAME)
    project_name_escaped = quote(PROJECT_NAME)
    devops_headers = {"Authorization": f"Basic {encode_pat()}"}
    return org_name_escaped, project_name_escaped, devops_headers


async def fetch_initial_data(session, query_id):
    """Fetch initial data such as work item icons and work items."""
    work_item_type_to_icon = await get_icons(session, ORG_NAME, PROJECT_NAME)
    work_items = await get_items(session, ORG_NAME, PROJECT_NAME, query_id)
    return work_item_type_to_icon, work_items


async def fetch_and_process_work_items(
    session, org_name_escaped, project_name_escaped, work_items
):
    """Fetch and process parent work items and group them."""
    parent_child_groups = group_items(work_items)
    parent_work_items = await fetch_parent_items(
        session, org_name_escaped, project_name_escaped, parent_child_groups.keys()
    )
    add_other_parent(parent_work_items)
    return parent_work_items


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
        ORG_NAME,
        PROJECT_NAME,
        SOLUTION_NAME,
        RELEASE_VERSION,
        RELEASE_QUERY,
        GPT_API_KEY,
        PAT,
        MODEL,
        MODEL_BASE_URL,
        DEVOPS_BASE_URL,
        SOFTWARE_SUMMARY,
        DESIRED_WORK_ITEM_TYPES,
        OUTPUT_FOLDER,
        DEVOPS_API_VERSION,
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
        result = asyncio.run(write_notes(RELEASE_QUERY, "Resolved Issues", True, True))
        return result


if __name__ == "__main__":
    main()
