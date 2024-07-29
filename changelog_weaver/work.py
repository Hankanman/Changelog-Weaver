"""This module provides a wrapper class to abstract away the platform-specific details of fetching work items."""

from typing import List, Union, Dict, Optional

import logging as log

from .configuration import Config
from .typings.types import (
    HierarchicalWorkItem,
    WorkItemGroup,
    Platform,
    WorkItem,
    WorkItemType,
)

from .platforms import DevOpsConfig, DevOpsClient, GitHubConfig, GitHubClient


class Work:
    """This class provides a wrapper to abstract away the platform-specific details of fetching work items."""

    def __init__(self, config: Config):
        self.all = {}
        self.root_items = []
        self.by_type = []
        self.root_type = ""

        self.platform = config.project.platform
        self.organization = config.project.platform.organization
        self.project = config.project.ref

        if self.platform.platform == Platform.AZURE_DEVOPS:
            client_config = DevOpsConfig(
                url=config.project.platform.base_url,
                org=self.organization,
                project=self.project,
                query=config.project.platform.query,
                pat=config.project.platform.access_token,
            )
            self.devops = DevOpsClient(client_config)
            self.github = None
        elif self.platform.platform == Platform.GITHUB:
            self.github = GitHubClient(
                GitHubConfig(
                    access_token=config.project.platform.access_token,
                    repo_name=config.project.ref,
                )
            )
            self.devops = None
        else:
            raise ValueError(f"Unsupported platform: {self.platform}")

    async def initialize(self):
        """Initialize the client."""
        if self.devops:
            await self.devops.initialize()
        elif self.github:
            await self.github.initialize()
        self.root_type = self._get_root_work_item_type()

    def add(self, work_item: WorkItem):
        """Add a work item to the collection."""
        self.all[work_item.id] = work_item
        return self.all

    async def get_item_by_id(self, item_id: Union[int, str]) -> HierarchicalWorkItem:
        """Retrieve details for a specific work item."""
        if self.devops:
            item = await self.devops.get_work_item_by_id(int(item_id))
        elif self.github:
            item = await self.github.get_issue_by_number(int(item_id))

        self.add(item)
        return self._convert_to_hierarchical(item)

    async def get_items_from_query(self, query: str) -> List[HierarchicalWorkItem]:
        """Retrieve work items based on a search query."""
        if self.devops:
            items = await self.devops.get_work_items_from_wiql(query)
        elif self.github:
            items = await self.github.get_issues_from_query(query)
        else:
            items = []

        for item in items:
            self.add(item)
        return self._build_hierarchy(items)

    async def get_items_with_details(self, **kwargs) -> List[HierarchicalWorkItem]:
        """Retrieve work items with details."""
        if self.devops:
            items = await self.devops.get_work_items_from_query(**kwargs)
        elif self.github:
            items = await self.github.get_issues_with_details(**kwargs)
        else:
            items = []

        for item in items:
            self.add(item)

        for item in items:
            await self._get_parent(item)

        self._create_other_parent()
        self._work_item_tree()

        self.by_type = self._group_by_type(self.root_items)

        return self._build_hierarchy(list(self.all.values()))

    def get_work_item_types(self) -> List[WorkItemType]:
        """Get all work item types."""
        if self.devops:
            return self.devops.get_all_work_item_types()
        if self.github:
            return self.github.get_all_issue_types()
        return []

    def get_work_item_type(self, type_name: str) -> Optional[WorkItemType]:
        """Get a work item type by name."""
        if self.devops:
            return self.devops.get_work_item_type(type_name)
        if self.github:
            return self.github.get_issue_type(type_name)
        return None

    async def generate_ordered_work_items(self) -> List[WorkItemGroup]:
        """Generate an ordered list of work items grouped by type."""
        if self.devops:
            all_items = await self.get_items_with_details(
                query_id=self.devops.config.query
            )
        elif self.github:
            all_items = await self.get_items_with_details()
        return self._group_children_by_type(all_items)

    def _remove_child_from_workitem(self, parent_id: int, child_id: int):
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

    def _create_other_parent(self):
        """Create an 'Other' parent for orphaned items."""
        orphaned_items = [
            item for item in self.all.values() if item.orphan and item.id != 0
        ]

        if orphaned_items:
            log.info("Creating 'Other' work item for orphaned items")
            other_parent = WorkItem(
                type="Other",
                root=True,
                orphan=False,
                id=0,
                title="Other",
                state="Other",
                comment_count=0,
                parent_id=0,
                icon="https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_review?color=333333&v=2",
                children=orphaned_items,
            )
            self.add(other_parent)

            # Update the parent_id of orphaned items
            for item in orphaned_items:
                item.parent_id = 0
                item.orphan = False

    def _work_item_tree(self) -> None:
        """Build a tree structure of work items."""
        self.root_items = []
        other_parent = None

        for item in self.all.values():
            if item.id == 0:  # This is the "Other" parent
                other_parent = item
                continue

            if item.parent_id and item.parent_id in self.all:
                parent_item = self.all[item.parent_id]
                if not hasattr(parent_item, "children"):
                    parent_item.children = []
                parent_item.children.append(item)
            elif item.root and not item.orphan:
                self.root_items.append(item)

        # Add the "Other" parent to root_items if it has children
        if other_parent and other_parent.children:
            self.root_items.append(other_parent)

    def _group_by_type(self, items: List[WorkItem]) -> List[WorkItemGroup]:
        """Group work items by their type while preserving hierarchy."""
        grouped_items = {}
        for item in items:
            if item.type not in grouped_items:
                grouped_items[item.type] = []
            grouped_items[item.type].append(item)

        grouped_children_list = []
        for key, value in grouped_items.items():
            grouped_children_list.append(
                WorkItemGroup(
                    type=key, icon=value[0].icon, items=self._group_children(value)
                )
            )

        # Ensure "Other" group is at the end of the list
        other_group = next(
            (group for group in grouped_children_list if group.type == "Other"), None
        )
        if other_group:
            grouped_children_list.remove(other_group)
            grouped_children_list.append(other_group)

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
                    WorkItemGroup(
                        type=key, icon=value[0].icon, items=self._group_children(value)
                    )
                    for key, value in grouped_children.items()
                ]
        return items

    async def _get_parent(self, item: WorkItem):
        """Recursively fetch parent work items and add them to the list asynchronously."""

        if item.parent_id and item.parent_id not in self.all:
            parent_item = await self.get_item_by_id(item.parent_id)
            await self._get_parent(parent_item)

    def _convert_to_hierarchical(self, item: WorkItem) -> HierarchicalWorkItem:
        """Convert a WorkItem to a HierarchicalWorkItem."""
        hierarchical_item = HierarchicalWorkItem(**item.__dict__)
        hierarchical_item.children = [
            self._convert_to_hierarchical(child) for child in item.children
        ]
        if item.id == 0:  # Special handling for "Other" parent
            hierarchical_item.children_by_type = self._group_children_by_type(
                hierarchical_item.children
            )
            hierarchical_item.children = (
                []
            )  # Clear children as they're now in children_by_type
        else:
            hierarchical_item.children_by_type = []
        return hierarchical_item

    def _build_hierarchy(self, items: List[WorkItem]) -> List[HierarchicalWorkItem]:
        """Build a hierarchical structure from a flat list of work items."""
        item_map: Dict[int, HierarchicalWorkItem] = {}
        root_items: List[HierarchicalWorkItem] = []

        # First pass: create HierarchicalWorkItems and build item_map
        for item in items:
            hierarchical_item = self._convert_to_hierarchical(item)
            item_map[item.id] = hierarchical_item

        # Second pass: build the hierarchy
        for item in item_map.values():
            if item.parent_id and item.parent_id in item_map:
                parent = item_map[item.parent_id]
                if item not in parent.children:
                    parent.children.append(item)
            elif item.id == 0 or (item.root and not item.orphan):
                root_items.append(item)

        # Third pass: group children by type for root items (except "Other")
        for item in root_items:
            if item.id != 0:  # Skip "Other" parent
                item.children_by_type = self._group_children_by_type(item.children)

        return root_items

    def _group_children_by_type(
        self, children: List[HierarchicalWorkItem]
    ) -> List[WorkItemGroup]:
        """Group children by their type."""
        type_groups: Dict[str, WorkItemGroup] = {}
        for child in children:
            if child.type not in type_groups:
                type_groups[child.type] = WorkItemGroup(
                    type=child.type, icon=child.icon, items=[]
                )
            type_groups[child.type].items.append(child)
        return list(type_groups.values())

    def _get_root_work_item_type(self) -> str:
        """Get the root work item type based on the backlog configuration."""
        if self.devops:
            return self.devops.root_work_item_type
        return ""
