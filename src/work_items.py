""" WorkItems Definitions """

from __future__ import annotations

import os
import asyncio
import json
import logging as log
import re
from typing import List, Optional
from dataclasses import fields

import aiohttp

from src.config import Config
from src.utils import clean_string, send_request
from src.item_types import ItemTypes
from src._types import Comment, WorkItem, WorkItemChildren, User


class WorkItems:
    """Manages the list of all work items and related operations."""

    def __init__(self):
        self.all = {}
        self.by_type = []
        self.types = ItemTypes()
        self.all_ids = set()
        self.item_locks = {}
        self.root_items = []

    def add_work_item(self, work_item: WorkItem):
        """Add a work item to the list."""
        if work_item.id not in self.all_ids:
            self.all[work_item.id] = work_item
            self.all_ids.add(work_item.id)

    def get_work_item(self, item_id: int) -> Optional[WorkItem]:
        """Get a work item by its ID."""
        return self.all.get(item_id)

    async def get_items(
        self,
        config: Config,
        summarise: bool = True,
    ) -> List[WorkItem]:
        """Fetch the list of work item IDs and return the ordered work items."""
        if self.types.all == {}:
            await self.types.get(config)
        uri = f"{config.devops.url}/{config.devops.org}/{config.devops.project}/_apis/wit/wiql/{config.devops.query}"
        headers = {"Authorization": f"Basic {config.devops.pat}"}

        result = await send_request(uri, headers=headers)

        work_item_ids = [item["id"] for item in result["workItems"]]

        log.info("Fetched %s Work Item IDs", len(work_item_ids))
        log.info("Fetching Work Item Details...")

        tasks = [
            self.fetch_item(config, item_id, summarise) for item_id in work_item_ids
        ]
        await asyncio.gather(*tasks, return_exceptions=False)

        log.info("Fetched %s Work Items", len(self.all))

        # Build the tree structure
        self.work_item_tree()

        work_item_zero = self.get_work_item(0)
        if work_item_zero and hasattr(work_item_zero, "children"):
            other_items = [
                item for item in work_item_zero.children if len(item.children) > 0
            ]
            for item in other_items:
                self.remove_child_from_workitem(0, item.id)

        self.by_type = self.group_by_type(self.get_root_items())

        return list(self.all.values())

    def remove_child_from_workitem(self, parent_id: int, child_id: int):
        """Remove a child from a parent work item."""
        # Retrieve the parent WorkItem
        parent_item = self.all.get(parent_id)

        # Check if the parent WorkItem exists and has children
        if parent_item and hasattr(parent_item, "children"):
            # Find the child to remove by ID
            child_to_remove = next(
                (child for child in parent_item.children if child.id == child_id), None
            )

            # If the child was found, remove it
            if child_to_remove:
                parent_item.children.remove(child_to_remove)
                log.info(
                    "Removed child with ID %s from parent with ID %s",
                    child_id,
                    parent_id,
                )
            else:
                log.info(
                    "Child with ID %s not found in parent with ID %s",
                    child_id,
                    parent_id,
                )
        else:
            log.info(
                "Parent with ID %s not found or has no children",
                parent_id,
            )

    async def fetch_item(
        self,
        config: Config,
        item_id: int,
        get_summary: bool = True,
    ) -> WorkItem:
        """Fetch a work item by its ID asynchronously."""

        # Ensure there is a lock for the item_id
        if item_id not in self.item_locks:
            self.item_locks[item_id] = asyncio.Lock()

        async with self.item_locks[item_id]:
            if item_id in self.all_ids:
                log.debug("Work Item %s already fetched", item_id)
                return self.all[item_id]
            try:
                fields = ",".join(config.devops.fields)
                uri = f"{config.devops.url}/{config.devops.org}/{config.devops.project}/_apis/wit/workitems/{item_id}?fields={fields}"
                headers = {"Authorization": f"Basic {config.devops.pat}"}
                log.info("Fetching Work Item: %s", item_id)
                item = await send_request(uri, headers=headers)
            except aiohttp.ClientResponseError:
                log.error("Error fetching Work Item: %s", item_id)

            work_item = WorkItem(
                id=item["id"],
                type=str(item["fields"]["System.WorkItemType"]),
                state=str(item["fields"]["System.State"]),
                comment_count=int(item["fields"]["System.CommentCount"]),
                parent=int(item["fields"].get("System.Parent") or 0),
                title=clean_string(item["fields"]["System.Title"], 3),
                story_points=int(
                    item["fields"].get("Microsoft.VSTS.Scheduling.StoryPoints") or 0
                ),
                priority=int(item["fields"].get("Microsoft.VSTS.Common.Priority") or 0),
                description=(
                    clean_string(item["fields"]["System.Description"])
                    if item["fields"].get("System.Description")
                    else ""
                ),
                repro_steps=(
                    clean_string(item["fields"]["Microsoft.VSTS.TCM.ReproSteps"])
                    if item["fields"].get("Microsoft.VSTS.TCM.ReproSteps")
                    else ""
                ),
                acceptance_criteria=(
                    clean_string(
                        item["fields"]["Microsoft.VSTS.Common.AcceptanceCriteria"]
                    )
                    if item["fields"].get("Microsoft.VSTS.Common.AcceptanceCriteria")
                    else ""
                ),
                tags=str(item["fields"].get("System.Tags")).split("; ") or [],
                url=re.sub(
                    r"_apis/wit/workitems",
                    "_workitems/edit",
                    item["url"],
                    flags=re.IGNORECASE,
                ),
            )
            work_item_type = self.types.get_type(work_item.type)
            if work_item_type:
                work_item.type = work_item_type.name
                work_item.icon = work_item_type.icon
            if work_item.comment_count != 0:
                work_item.comments = await self.fetch_comments(config, item_id)
            if work_item.parent not in self.all_ids and work_item.parent != 0:
                await self.get_parent(config, work_item, get_summary)

            if get_summary and not work_item.summary:
                log.info("Summarising Work Item: %s", work_item.id)
                content = (
                    f"ROLE: {config.prompts.item} "
                    f"TITLE: {work_item.title} "
                    f"DESCRIPTION: {work_item.description} "
                    f"REPRODUCTION_STEPS: {work_item.repro_steps} "
                    f"COMMENTS: {work_item.comments} "
                    f"ACCEPTANCE_CRITERIA: {work_item.acceptance_criteria}"
                )
                work_item.summary = await config.model.summarise(content)

        self.all[work_item.id] = work_item
        self.all_ids.add(work_item.id)
        return work_item

    async def fetch_comments(self, config: Config, item_id: int) -> List[str]:
        """Fetch comments for a work item asynchronously."""
        uri = f"{config.devops.url}/{config.devops.org}/{config.devops.project}/_apis/wit/workitems/{item_id}/comments"
        headers = {"Authorization": f"Basic {config.devops.pat}"}
        log.info("Fetching Comments for Work Item: %s", item_id)
        comments_data = await send_request(uri, headers=headers)

        comments = [
            Comment(
                text=comment["text"],
                modified_date=comment["modifiedDate"],
                modified_by=User(
                    display_name=comment["modifiedBy"]["displayName"],
                    url=comment["modifiedBy"]["url"],
                    user_id=comment["modifiedBy"]["id"],
                    unique_name=comment["modifiedBy"]["uniqueName"],
                ),
            )
            for comment in comments_data.get("comments", [])
        ]
        comments.sort(key=lambda comment: comment.modified_date, reverse=True)
        return [
            f"{comment.modified_date} | {comment.modified_by.display_name} | {comment.text}"
            for comment in comments
        ]

    async def get_parent(
        self,
        config: Config,
        item: WorkItem,
        get_summary: bool = True,
    ):
        """Recursively fetch parent work items and add them to the list asynchronously."""
        parent_id = item.parent
        if parent_id and not self.get_work_item(parent_id):
            parent_item = await self.fetch_item(config, parent_id, get_summary)
            await self.get_parent(config, parent_item, get_summary)

    def work_item_tree(self) -> None:
        """Build a tree structure of work items."""
        self.root_items = []
        other_items = []

        for item in self.all.values():
            parent_id = item.parent
            if parent_id:
                parent_item = self.all.get(parent_id)
                if parent_item:
                    if parent_item.children is None:
                        parent_item.children = []
                    parent_item.children.append(item)
                else:
                    log.warning(
                        "Parent work item %s not found for work item %s",
                        parent_id,
                        item.id,
                    )
            else:
                if item.type == "Other":
                    other_items.append(item)
                else:
                    self.root_items.append(item)

        # Create an "Other" work item at the top level if there are any items with no parent
        if other_items:
            other_parent = WorkItem(
                id=0,
                type="Other",
                state="Other",
                comment_count=0,
                parent=0,
                title="Other",
                icon="Other",
                children=other_items,
            )
            self.root_items.append(other_parent)

    def get_root_items(self) -> List[WorkItem]:
        """Get the root items of the work item tree."""
        return self.root_items

    def group_by_type(self, items: List[WorkItem]) -> List[WorkItemChildren]:
        """Group work items by their type while preserving hierarchy."""
        grouped_items = {}
        for item in items:
            if item.type not in grouped_items:
                grouped_items[item.type] = []
            grouped_items[item.type].append(item)

        grouped_children_list = []
        for key, value in grouped_items.items():
            if key == "Other":
                # For "Other" type, we want to include its children directly
                other_children = []
                for other_item in value:
                    other_children.extend(other_item.children)
                if other_children:  # Only add "Other" if it has children
                    grouped_children_list.append(
                        WorkItemChildren(
                            type="Other",
                            icon=value[0].icon,
                            items=self._group_children(other_children),
                        )
                    )
            else:
                grouped_children_list.append(
                    WorkItemChildren(
                        type=key, icon=value[0].icon, items=self._group_children(value)
                    )
                )

        return grouped_children_list

    def _group_children(self, items: List[WorkItem]) -> List[WorkItem]:
        """Recursively group the children of each work item by their type."""
        for item in items:
            if item.children:
                grouped_children = {}
                for child in item.children:
                    if child.type not in grouped_children:
                        grouped_children[child.type] = []
                    grouped_children[child.type].append(child)

                item.children_by_type = [
                    WorkItemChildren(
                        type=key, icon=value[0].icon, items=self._group_children(value)
                    )
                    for key, value in grouped_children.items()
                ]
        return items


async def main(output_json: bool, output_folder: str):
    """Main function to fetch work items and save them to a file."""
    config = Config()
    log.basicConfig(
        level=config.log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[log.StreamHandler()],
    )

    async with aiohttp.ClientSession() as session:
        wi = WorkItems()
        await wi.get_items(config)

    items = wi.all
    types = wi.types

    if output_json:
        # Convert types to JSON
        types_json = json.dumps([type for type in types.get_types()], indent=4)

        # Save types JSON to file
        os.makedirs(output_folder, exist_ok=True)

        with open(f"{output_folder}/types.json", "w", encoding="utf-8") as file:
            file.write(types_json)

        # Convert items to JSON
        items_json = json.dumps(
            [
                item.model_dump(exclude={"children", "children_by_type"})
                for item in wi.all.values()
            ],
            indent=4,
        )

        # Save items JSON to file
        with open(f"{output_folder}/work_items.json", "w", encoding="utf-8") as file:
            file.write(items_json)

        ordered_items_json = json.dumps(
            [item for item in wi.by_type],
            indent=4,
        )
        with open(
            f"{output_folder}/ordered_work_items.json", "w", encoding="utf-8"
        ) as file:
            file.write(ordered_items_json)
    await session.close()
    return items


if __name__ == "__main__":
    import argparse
    import time

    parser = argparse.ArgumentParser(
        description="Fetch and process work items from DevOps"
    )
    parser.add_argument("--output_json", action="store_true", help="Output JSON files")
    parser.add_argument(
        "--output_folder", type=str, default=".", help="Folder to save JSON files"
    )

    args = parser.parse_args()
    start_time = time.time()
    work_items = asyncio.run(main(args.output_json, args.output_folder))
    log.info(
        "Retrieved %s  Work Items in %s milliseconds",
        len(work_items),
        round((time.time() - start_time) * 1000),
    )
