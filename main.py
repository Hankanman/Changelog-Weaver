# main.py
import aiohttp
import asyncio
import base64
import logging as log
from pathlib import Path
from urllib.parse import quote
from collections import defaultdict
from modules.config import (
    ORG_NAME,
    PROJECT_NAME,
    SOLUTION_NAME,
    RELEASE_VERSION,
    RELEASE_QUERY,
    PAT,
    DEVOPS_BASE_URL,
    DESIRED_WORK_ITEM_TYPES,
    OUTPUT_FOLDER,
    GPT_API_KEY,
    SOFTWARE_SUMMARY,
    SUMMARY_PROMPT,
)
from modules.enums import WorkItemType, WorkItemField, APIEndpoint
from modules.utils import (
    setupLogs,
    cleanString,
    getWorkItemIcons,
    getWorkItems,
    updateItemGroup,
    finaliseNotes,
)
from markdown_it import MarkdownIt


async def write_release_notes(
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
    md = MarkdownIt()

    with open(file_md, "w", encoding="utf-8") as file:
        file.write(
            md.render(
                f"# Release Notes for {SOLUTION_NAME} version v{RELEASE_VERSION}\n\n## Summary\n\n<NOTESSUMMARY>\n\n## Quick Links\n\n<TABLEOFCONTENTS>"
            )
        )

    section_headers.append(section_header)
    async with aiohttp.ClientSession(headers=devops_headers) as session:
        work_item_type_to_icon = await getWorkItemIcons(session, ORG_NAME, PROJECT_NAME)

        # Write the section header to the file
        with open(file_md, "a", encoding="utf-8") as file:
            file.write(md.render(f"## {section_header}\n---\n"))

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
                log.warning(f"Work item {item['id']} has no parent")
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

        for work_item_type in DESIRED_WORK_ITEM_TYPES:
            log.info(f"Processing {work_item_type}s")

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
                log.info(f"{work_item_type} | {parent_id} | {parent_title}")

                parent_link = parent_work_item["_links"]["html"]["href"]
                parent_icon_url = work_item_type_to_icon.get(work_item_type)["iconUrl"]

                child_items = [
                    wi
                    for wi in work_items
                    if wi["fields"].get(WorkItemField.PARENT.value) == int(parent_id)
                ]
                if not child_items:
                    log.info(f"No child items found for parent {parent_id}")

                summary_notes += f"- {parent_title}\n"
                parent_header = f"\n### <img src='{parent_icon_url}' alt='icon' width='20' height='20'> [#{parent_id}]({parent_link}) {parent_title}"

                grouped_child_items = defaultdict(list)
                for item in child_items:
                    grouped_child_items[
                        item["fields"][WorkItemField.WORK_ITEM_TYPE.value]
                    ].append(item)

                if grouped_child_items:
                    with open(file_md, "a", encoding="utf-8") as file:
                        file.write(md.render(parent_header))
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
    # check if the environment variables are set and exit if not
    required_env_vars = [
        ORG_NAME,
        PROJECT_NAME,
        SOLUTION_NAME,
        RELEASE_VERSION,
        RELEASE_QUERY,
        PAT,
        GPT_API_KEY,
    ]
    if any(not var for var in required_env_vars):
        log.error(
            "Please set the environment variables in the .env file before running the script."
        )
        exit(1)
    else:
        asyncio.run(write_release_notes(RELEASE_QUERY, "Resolved Issues", True, False))
