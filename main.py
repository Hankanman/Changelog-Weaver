""" Main script to write release notes based on Azure DevOps work items. """
import base64
import sys
import logging as log
from pathlib import Path
from urllib.parse import quote
from collections import defaultdict
import asyncio
import aiohttp
from modules.config import (
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
from modules.enums import WorkItemField, APIEndpoint
from modules.utils import (
    setupLogs,
    cleanString,
    getWorkItemIcons,
    getWorkItems,
    updateItemGroup,
    finaliseNotes,
)


async def writeReleaseNotes(
    query_id: str, section_header: str, summarize_items: bool, output_html: bool
):
    """
    Main function to write release notes based on Azure DevOps work items.
    """
    org_name_escaped = quote(ORG_NAME)
    project_name_escaped = quote(PROJECT_NAME)
    pat_encoded = base64.b64encode(f":{PAT}".encode()).decode()

    devops_headers = {"Authorization": f"Basic {pat_encoded}"}

    folder_path = Path(".") / OUTPUT_FOLDER
    file_md = (folder_path / f"{SOLUTION_NAME}-v{RELEASE_VERSION}.md").resolve()
    file_html = (folder_path / f"{SOLUTION_NAME}-v{RELEASE_VERSION}.html").resolve()
    folder_path.mkdir(parents=True, exist_ok=True)

    summary_notes = ""
    section_headers = []

    with open(file_md, "w", encoding="utf-8") as md_file:
        md_file.write(
            f"# Release Notes for {SOLUTION_NAME} version v{RELEASE_VERSION}\n\n"
            f"## Summary\n\n"
            f"<NOTESSUMMARY>\n\n"
            f"## Quick Links\n\n"
            f"<TABLEOFCONTENTS>\n"
        )

    section_headers.append(section_header)
    async with aiohttp.ClientSession(headers=devops_headers) as session:
        work_item_type_to_icon = await getWorkItemIcons(session, ORG_NAME, PROJECT_NAME)

        # Write the section header to the file
        with open(file_md, "a", encoding="utf-8") as md_file:
            md_file.write(f"## {section_header}\n")

        work_items = await getWorkItems(session, ORG_NAME, PROJECT_NAME, query_id)

        parent_child_groups = defaultdict(list)
        parent_work_items = {}

        # Group work items by their parent
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

        parents = {
            key: value for (key, value) in parent_child_groups.items() if key != "0"
        }
        for parent_id in parents.keys():
            parent_uri = DEVOPS_BASE_URL + APIEndpoint.WORK_ITEM.value.format(
                org_name=org_name_escaped,
                project_name=project_name_escaped,
                parent_id=parent_id,
            )
            async with session.get(parent_uri) as parent_response:
                parent_work_items[parent_id] = await parent_response.json()

        # Add a placeholder for items with no parent
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

        for work_item_type in DESIRED_WORK_ITEM_TYPES:
            log.info("Processing %s s", {work_item_type})

            parent_ids_of_type = [
                pid
                for pid, item in parent_work_items.items()
                if item["fields"]["System.WorkItemType"] == work_item_type
            ]

            for parent_id in parent_ids_of_type:
                parent_work_item = parent_work_items[parent_id]
                parent_title = cleanString(
                    parent_work_item["fields"][WorkItemField.TITLE.value]
                )
                log.info("%s | %s | %s", work_item_type, parent_id, parent_title)

                parent_link = parent_work_item["_links"]["html"]["href"]
                parent_icon_url = work_item_type_to_icon.get(work_item_type)["iconUrl"]

                child_items = [
                    wi
                    for wi in work_items
                    if wi["fields"].get(WorkItemField.PARENT.value) == int(parent_id)
                ]
                if not child_items:
                    log.info("No child items found for parent %s", parent_id)

                summary_notes += f"- {parent_title}\n"
                if parent_id != "0":
                    parent_head_link = f"[#{parent_id}]({parent_link}) "
                else:
                    parent_head_link = ""
                parent_header = (
                    f"\n### <img src='{parent_icon_url}' alt='icon' width='20' height='20'> "
                    f"{parent_head_link}{parent_title}\n"
                )

                grouped_child_items = defaultdict(list)
                for item in child_items:
                    grouped_child_items[
                        item["fields"][WorkItemField.WORK_ITEM_TYPE.value]
                    ].append(item)

                if grouped_child_items:
                    with open(file_md, "a", encoding="utf-8") as file_output:
                        file_output.write(parent_header)
                    await updateItemGroup(
                        summary_notes,
                        grouped_child_items,
                        work_item_type_to_icon,
                        file_md,
                        session,
                        summarize_items,
                    )

        await finaliseNotes(
            output_html, summary_notes, file_md, file_html, section_headers
        )


if __name__ == "__main__":
    setupLogs()
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
        asyncio.run(writeReleaseNotes(RELEASE_QUERY, "Resolved Issues", True, True))
