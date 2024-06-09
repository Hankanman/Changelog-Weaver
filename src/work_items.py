""" WorkItems Definitions """

from __future__ import annotations

import asyncio
import base64
import json
import logging as log
import re
from typing import List, Optional, Union

import aiohttp
from pydantic import BaseModel, Field, field_validator, model_validator

from src.config import DevOpsConfig, Prompts, Config
from src.utils import clean_string, format_date, summarise


async def get_items(
    session: aiohttp.ClientSession,
    manager: WorkItemManager,
    type_manager: TypeManager,
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
        fetch_item(session, item_id, manager, type_manager, get_summary)
        for item_id in work_item_ids
    ]
    await asyncio.gather(*tasks)

    log.debug("Fetched all WorkItems")

    # Initialize parents for all work items
    parent_tasks = [
        item.init_parent(session, manager, type_manager)
        for item in manager.all_work_items
    ]
    await asyncio.gather(*parent_tasks)

    log.debug("Initialized parents for all WorkItems")

    return manager.build_work_item_tree()


async def fetch_item(
    session: aiohttp.ClientSession,
    item_id: int,
    manager: WorkItemManager,
    type_manager: TypeManager,
    get_summary: bool = True,
) -> WorkItem:
    """Fetch a work item by its ID asynchronously."""
    # Check if the work item is already in the manager
    existing_item = manager.get_work_item(item_id)
    if existing_item:
        return existing_item

    fields = ",".join(DevOpsConfig.fields)
    uri = f"{DevOpsConfig.devops_base_url}/{DevOpsConfig.org_name}/{DevOpsConfig.project_name}/_apis/wit/workitems/{item_id}?fields={fields}"
    headers = {
        "Authorization": f"Basic {base64.b64encode(f':{DevOpsConfig.pat}'.encode()).decode()}"
    }

    async with session.get(uri, headers=headers, timeout=10) as response:
        item = await response.json()

    work_item = WorkItem(**item["fields"], id=item["id"], url=item["url"])
    work_item_type = type_manager.get_type(work_item.workItemType)
    if work_item_type:
        work_item.type = work_item_type.name
        work_item.icon = work_item_type.icon.url
    if work_item.commentCount != 0:
        work_item.comments = await fetch_comments(session, item_id)

    manager.add_work_item(work_item)

    await manager.fetch_parents_recursively(session, work_item, type_manager)

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


async def fetch_comments(session: aiohttp.ClientSession, item_id: int) -> List[str]:
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


class WorkItemManager:
    """Manages the list of all work items and related operations."""

    def __init__(self):
        self.all_work_items = []

    def add_work_item(self, work_item: WorkItem):
        """Add a work item to the list."""
        if work_item not in self.all_work_items:
            self.all_work_items.append(work_item)

    def get_work_item(self, item_id: int) -> Optional[WorkItem]:
        """Get a work item by its ID."""
        return next((wi for wi in self.all_work_items if wi.id == item_id), None)

    async def fetch_parents_recursively(
        self,
        session: aiohttp.ClientSession,
        item: WorkItem,
        type_manager: TypeManager,
    ):
        """Recursively fetch parent work items and add them to the list asynchronously."""
        parent_id = item.parent
        if parent_id and not self.get_work_item(parent_id):
            try:
                parent_item = await fetch_item(session, parent_id, self, type_manager)
                await self.fetch_parents_recursively(session, parent_item, type_manager)
            except aiohttp.ClientError as e:
                log.warning("Failed to fetch parent work item %s: %s", parent_id, e)

    def build_work_item_tree(self) -> List[WorkItem]:
        """Build a tree structure of work items."""
        work_item_map = {item.id: item for item in self.all_work_items}
        root_items = []

        for item in self.all_work_items:
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

        return root_items


class TypeManager:
    """Manages the list of all work item types."""

    def __init__(self):
        self.types = {}

    async def fetch_types(self, session: aiohttp.ClientSession):
        """Fetch work item types asynchronously."""
        uri = f"{DevOpsConfig.devops_base_url}/{DevOpsConfig.org_name}/{DevOpsConfig.project_name}/_apis/wit/workitemtypes"
        headers = {
            "Authorization": f"Basic {base64.b64encode(f':{DevOpsConfig.pat}'.encode()).decode()}"
        }

        async with session.get(uri, headers=headers, timeout=10) as response:
            types_data = await response.json()

        self.types = {
            type["name"]: WorkItemType(**type) for type in types_data.get("value", [])
        }

    def get_type(self, type_name: str) -> Optional[WorkItemType]:
        """Get a work item type by name."""
        return self.types.get(type_name)


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


class Icon(BaseModel):
    """Represents an icon for a work item."""

    id: str
    url: str


class WorkItemType(BaseModel):
    """Represents a work item type."""

    name: str
    icon: Icon


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


class WorkItem(BaseModel):
    """Represents a work item."""

    id: int
    workItemType: str = Field(..., alias="System.WorkItemType")
    state: str = Field(..., alias="System.State")
    commentCount: int = Field(..., alias="System.CommentCount")
    title: str = Field(..., alias="System.Title")
    description: Optional[str] = Field(None, alias="System.Description")
    reproSteps: Optional[str] = Field(None, alias="Microsoft.VSTS.TCM.ReproSteps")
    acceptanceCriteria: Optional[str] = Field(
        None, alias="Microsoft.VSTS.Common.AcceptanceCriteria"
    )
    tags: Optional[Union[str, List[str]]] = Field(None, alias="System.Tags")
    parent: Optional[int] = Field(None, alias="System.Parent")
    url: str
    comments: Optional[List[str]] = None
    type: Optional[str] = None
    icon: Optional[str] = None
    parent_work_item: Optional[WorkItem] = None
    children: Optional[List[WorkItem]] = []
    summary: Optional[str] = None

    async def init_parent(
        self,
        session: aiohttp.ClientSession,
        manager: WorkItemManager,
        type_manager: TypeManager,
    ):
        """Initialize the parent work item."""
        if self.parent:
            self.parent_work_item = await fetch_item(
                session, self.parent, manager, type_manager
            )

    def parent_child(self, manager: WorkItemManager):
        """Dump the model to a dictionary, optionally excluding the parent attribute."""
        data = {
            "id": self.id,
            "workItemType": self.workItemType,
            "title": self.title,
            "summary": self.summary,
            "state": self.state,
            "commentCount": self.commentCount,
            "description": self.description,
            "reproSteps": self.reproSteps,
            "acceptanceCriteria": self.acceptanceCriteria,
            "tags": self.tags,
            "parent": self.parent,
            "url": self.url,
            "comments": self.comments,
            "type": self.type,
            "icon": self.icon,
            "children": [
                child.parent_child(manager) for child in (self.children or [])
            ],
        }
        return data

    @model_validator(mode="before")
    def set_url(cls, values):
        """Set the edit URL."""
        url = values.get("url")
        if url:
            values["url"] = re.sub(
                r"_apis/wit/workitems", "_workitems/edit", url, flags=re.IGNORECASE
            )
        return values

    @field_validator("tags", mode="before")
    def split_tags(cls, v):
        """Split tags into a list if it is a string."""
        if isinstance(v, str):
            return v.split("; ")
        return v

    @field_validator(
        "title", "description", "reproSteps", "acceptanceCriteria", mode="before"
    )
    def clean_fields(cls, v):
        """Clean the specified field."""
        if v:
            return clean_string(v)
        return v


async def main(output_json: bool, output_folder: str):
    """Main function to fetch work items and save them to a file."""
    log.basicConfig(level=log.WARNING)
    manager = WorkItemManager()
    type_manager = TypeManager()

    async with aiohttp.ClientSession() as session:
        await type_manager.fetch_types(session)
        ordered_work_items = await get_items(session, manager, type_manager, True)

    if output_json:
        # Convert types to JSON
        types_json = json.dumps(
            [type.model_dump() for type in type_manager.types.values()], indent=4
        )

        # Save types JSON to file
        with open(f"{output_folder}/types.json", "w", encoding="utf-8") as file:
            file.write(types_json)

        # Convert items to JSON
        items_json = json.dumps(
            [item.parent_child(manager) for item in manager.all_work_items], indent=4
        )

        # Save items JSON to file
        with open(f"{output_folder}/work_items.json", "w", encoding="utf-8") as file:
            file.write(items_json)

        # Convert ordered items to JSON
        ordered_items_json = json.dumps(
            [item.parent_child(manager) for item in ordered_work_items], indent=4
        )

        # Save ordered JSON to file
        with open(
            f"{output_folder}/work_items_ordered.json", "w", encoding="utf-8"
        ) as ordered_file:
            ordered_file.write(ordered_items_json)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch and process work items from DevOps"
    )
    parser.add_argument("--output_json", action="store_true", help="Output JSON files")
    parser.add_argument(
        "--output_folder", type=str, default=".", help="Folder to save JSON files"
    )

    args = parser.parse_args()

    asyncio.run(main(True, str(Config().output_folder)))
