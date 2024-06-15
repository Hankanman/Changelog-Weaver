""" WorkItems Definitions """

from __future__ import annotations

import os
import asyncio
import base64
import json
import logging as log
import re
from typing import List, Optional

import aiohttp
from pydantic import BaseModel, Field, field_validator

from src.config import DevOpsConfig, Prompts
from src.utils import clean_string, format_date, summarise


class WorkItems:
    """Manages the list of all work items and related operations."""

    def __init__(self):
        self.items = []
        self.ordered_items = []

    @classmethod
    async def initialize(cls, session: aiohttp.ClientSession):
        """Create a new instance of WorkItems."""
        self = WorkItems()
        item_types = await Types.initialize(session)
        await self.get_items(session, item_types, True)
        self.ordered_items = self.group_by_type(self.build_work_item_tree())
        return self

    def add_work_item(self, work_item: WorkItem):
        """Add a work item to the list."""
        if work_item not in self.items:
            self.items.append(work_item)

    def get_work_item(self, item_id: int) -> Optional[WorkItem]:
        """Get a work item by its ID."""
        return next((wi for wi in self.items if wi.id == item_id), None)

    async def get_items(
        self,
        session: aiohttp.ClientSession,
        item_types: Types,
        get_summary: bool = True,
    ) -> List[WorkItem]:
        """Fetch the list of work item IDs and return the ordered work items."""
        uri = f"{DevOpsConfig.devops_base_url}/{DevOpsConfig.org_name}/{DevOpsConfig.project_name}/_apis/wit/wiql/{DevOpsConfig.release_query}"
        headers = {
            "Authorization": f"Basic {base64.b64encode(f':{DevOpsConfig.pat}'.encode()).decode()}"
        }

        async with session.get(uri, headers=headers, timeout=10) as response:
            result = await response.json()

        work_item_ids = [item["id"] for item in result["workItems"]]

        tasks = [
            self.fetch_item(session, item_id, item_types, get_summary)
            for item_id in work_item_ids
        ]
        await asyncio.gather(*tasks)

        log.debug("Fetched all WorkItems")

        self.items.sort(key=lambda item: item.id)
        return self.items

    async def fetch_item(
        self,
        session: aiohttp.ClientSession,
        item_id: int,
        item_types: Types,
        get_summary: bool = True,
    ) -> WorkItem:
        """Fetch a work item by its ID asynchronously."""
        # Check if the work item is already in the work_items
        existing_item = self.get_work_item(item_id)
        if existing_item:
            return existing_item

        fields = ",".join(DevOpsConfig.fields)
        uri = f"{DevOpsConfig.devops_base_url}/{DevOpsConfig.org_name}/{DevOpsConfig.project_name}/_apis/wit/workitems/{item_id}?fields={fields}"
        headers = {
            "Authorization": f"Basic {base64.b64encode(f':{DevOpsConfig.pat}'.encode()).decode()}"
        }

        async with session.get(uri, headers=headers, timeout=10) as response:
            item = await response.json()

        work_item = WorkItem(
            **item["fields"],
            id=item["id"],
            type=str(item["fields"]["System.WorkItemType"]),
            state=str(item["fields"]["System.State"]),
            commentCount=int(item["fields"]["System.CommentCount"]),
            parent=int(item["fields"].get("System.Parent") or 0),
            title=clean_string(item["fields"]["System.Title"], 3),
            storyPoints=int(
                item["fields"].get("Microsoft.VSTS.Scheduling.StoryPoints") or 0
            ),
            priority=int(item["fields"].get("Microsoft.VSTS.Common.Priority") or 0),
            description=(
                clean_string(item["fields"]["System.Description"])
                if item["fields"].get("System.Description")
                else ""
            ),
            reproSteps=(
                clean_string(item["fields"]["Microsoft.VSTS.TCM.ReproSteps"])
                if item["fields"].get("Microsoft.VSTS.TCM.ReproSteps")
                else ""
            ),
            acceptanceCriteria=(
                clean_string(item["fields"]["Microsoft.VSTS.Common.AcceptanceCriteria"])
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
        work_item_type = item_types.get_type(work_item.type)
        if work_item_type:
            work_item.type = work_item_type.name
            work_item.icon = work_item_type.icon
        if work_item.commentCount != 0:
            work_item.comments = await self.fetch_comments(session, item_id)

        self.add_work_item(work_item)

        await self.get_parent(session, work_item, item_types)

        if get_summary:
            content = (
                f"ROLE: {Prompts.item} "
                f"TITLE: {work_item.title} "
                f"DESCRIPTION: {work_item.description} "
                f"REPRODUCTION_STEPS: {work_item.reproSteps} "
                f"COMMENTS: {work_item.comments} "
                f"ACCEPTANCE_CRITERIA: {work_item.acceptanceCriteria}"
            )
            work_item.summary = await summarise(content, session)
        else:
            work_item.summary = ""

        return work_item

    async def fetch_comments(
        self, session: aiohttp.ClientSession, item_id: int
    ) -> List[str]:
        """Fetch comments for a work item asynchronously."""
        uri = f"{DevOpsConfig.devops_base_url}/{DevOpsConfig.org_name}/{DevOpsConfig.project_name}/_apis/wit/workitems/{item_id}/comments"
        headers = {
            "Authorization": f"Basic {base64.b64encode(f':{DevOpsConfig.pat}'.encode()).decode()}"
        }

        async with session.get(uri, headers=headers, timeout=10) as response:
            comments_data = await response.json()

        comments = [Comment(**comment) for comment in comments_data.get("comments", [])]
        comments.sort(key=lambda comment: comment.modifiedDate, reverse=True)
        return [
            f"{comment.modifiedDate} | {comment.modifiedBy.displayName} | {comment.text}"
            for comment in comments
        ]

    async def get_parent(
        self,
        session: aiohttp.ClientSession,
        item: WorkItem,
        item_types: Types,
        get_summary: bool = True,
    ):
        """Recursively fetch parent work items and add them to the list asynchronously."""
        parent_id = item.parent
        if parent_id and not self.get_work_item(parent_id):
            try:
                parent_item = await self.fetch_item(
                    session, parent_id, item_types, get_summary
                )
                await self.get_parent(session, parent_item, item_types)
            except aiohttp.ClientError as e:
                log.warning("Failed to fetch parent work item %s: %s", parent_id, e)

    def build_work_item_tree(self) -> List[WorkItem]:
        """Build a tree structure of work items."""
        work_item_map = {item.id: item for item in self.items}
        root_items = []

        for item in self.items:
            parent_id = item.parent
            if parent_id:
                parent_item = work_item_map.get(parent_id)
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
                root_items.append(item)
                print(f"Root item: {item.id}")

        return root_items

    def group_by_type(self, items: List[WorkItem]) -> List[WorkItemChildren]:
        """Group work items by their type while preserving hierarchy."""
        grouped_items = {}
        for item in items:
            if item.type not in grouped_items:
                grouped_items[item.type] = []
            grouped_items[item.type].append(item)

        grouped_children_list = [
            WorkItemChildren(
                type=key, icon=value[0].icon, items=self._group_children(value)
            )
            for key, value in grouped_items.items()
        ]

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


class Types:
    """Manages the list of all work item types."""

    def __init__(self):
        self.all = {}

    @classmethod
    async def initialize(cls, session: aiohttp.ClientSession):
        """Create a new instance of Types."""
        self = Types()
        self.all = await self.fetch_types(session)
        return self

    async def fetch_types(self, session: aiohttp.ClientSession):
        """Fetch work item types asynchronously."""
        uri = f"{DevOpsConfig.devops_base_url}/{DevOpsConfig.org_name}/{DevOpsConfig.project_name}/_apis/wit/workitemtypes"
        headers = {
            "Authorization": f"Basic {base64.b64encode(f':{DevOpsConfig.pat}'.encode()).decode()}"
        }

        async with session.get(uri, headers=headers, timeout=10) as response:
            types_data = await response.json()

        types = {
            type["name"]: WorkItemType(
                name=type["name"],
                icon=type["icon"]["url"],
                color=str.format("#{}", type["color"]),
            )
            for type in types_data.get("value")
        }
        return types

    def get_type(self, type_name: str) -> Optional[WorkItemType]:
        """Get a work item type by name."""
        return self.all.get(type_name)

    def get_types(self) -> List[WorkItemType]:
        """Get all work item types."""
        return list(self.all.values())


# pylint: disable=no-self-argument
class User(BaseModel):
    """Represents a user."""

    displayName: str
    url: str
    id: str
    uniqueName: str

    @field_validator("displayName", mode="before")
    def clean_display_name(cls, v):
        """Clean the display name."""
        if isinstance(v, str):
            parts = v.split(".")
            if len(parts) == 2:
                return f"{parts[0].capitalize()} {parts[1].capitalize()}"
        return v


class WorkItemType(BaseModel):
    """Represents a work item type."""

    name: str
    icon: str
    color: str = "#000000"


# pylint: disable=invalid-name
class Comment(BaseModel):
    """Represents a comment on a work item."""

    text: str
    modifiedDate: str = Field(..., alias="modifiedDate")
    modifiedBy: User = Field(..., alias="modifiedBy")

    @field_validator("modifiedDate", mode="before")
    def format_date(cls, v):
        """Format the modified date."""
        return format_date(v)

    @field_validator("text", mode="before")
    def clean_text(cls, v):
        """Clean the text."""
        return clean_string(v)


class WorkItemChildren(BaseModel):
    """Represents a work item's children."""

    type: str
    icon: str = ""
    items: List[WorkItem]


class WorkItem(BaseModel):
    """Represents a work item."""

    id: int
    type: str = ""
    state: str
    commentCount: int = 0
    parent: int = 0
    title: str
    storyPoints: Optional[int] = None
    priority: Optional[int] = None
    summary: Optional[str] = None
    description: str
    reproSteps: str
    acceptanceCriteria: str
    tags: List[str] = []
    url: str = ""
    comments: List[str] = []
    icon: str = ""
    children: List[WorkItem] = []
    children_by_type: List[WorkItemChildren] = []


async def main(output_json: bool, output_folder: str):
    """Main function to fetch work items and save them to a file."""
    log.basicConfig(level=log.WARNING)
    async with aiohttp.ClientSession() as session:
        types = await Types.initialize(session)
        work_items = await WorkItems.initialize(session)

        if output_json:
            # Convert types to JSON
            types_json = json.dumps(
                [type.model_dump() for type in types.get_types()], indent=4
            )

            # Save types JSON to file
            os.makedirs(output_folder, exist_ok=True)

            with open(f"{output_folder}/types.json", "w", encoding="utf-8") as file:
                file.write(types_json)

            # Convert items to JSON
            items_json = json.dumps(
                [
                    item.model_dump(exclude={"children", "children_by_type"})
                    for item in work_items.items
                ],
                indent=4,
            )

            # Save items JSON to file
            with open(
                f"{output_folder}/work_items.json", "w", encoding="utf-8"
            ) as file:
                file.write(items_json)
    return work_items


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
    wi = asyncio.run(main(args.output_json, args.output_folder))
    print(
        "Retrieved",
        len(wi.items),
        "Work Items in",
        round((time.time() - start_time) * 1000),
        "milliseconds",
    )
