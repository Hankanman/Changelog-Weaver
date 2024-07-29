"""This module provides a wrapper class to abstract away the platform-specific details of fetching work items."""

from abc import ABC, abstractmethod
from typing import List, Union, Dict, Optional, Set

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


class PlatformClient(ABC):
    """This class provides an abstract base class for platform-specific clients."""

    @abstractmethod
    async def initialize(self):
        """Initialize the client."""

    @abstractmethod
    async def get_work_item_by_id(self, item_id: int) -> WorkItem:
        """Retrieve a work item by its ID."""

    @abstractmethod
    async def get_work_items_from_query(self, query_id: str) -> List[WorkItem]:
        """Retrieve work items based on a search query."""

    @abstractmethod
    async def get_work_items_with_details(self, **kwargs) -> List[WorkItem]:
        """Retrieve work items with details."""

    @abstractmethod
    def get_all_work_item_types(self) -> List[WorkItemType]:
        """Get all work item types."""

    @abstractmethod
    def get_work_item_type(self, type_name: str) -> Optional[WorkItemType]:
        """Get a work item type by name."""

    @property
    @abstractmethod
    def root_work_item_type(self) -> str:
        """Get the root work item type."""


class DevOpsPlatformClient(PlatformClient):
    """This class provides a platform-specific client for Azure DevOps."""

    def __init__(self, config: DevOpsConfig):
        self.client = DevOpsClient(config)
        self.query_id = config.query

    async def initialize(self):
        await self.client.initialize()

    async def get_work_item_by_id(self, item_id: int) -> WorkItem:
        return await self.client.get_work_item_by_id(item_id)

    async def get_work_items_from_query(self, query_id: str) -> List[WorkItem]:
        return await self.client.get_work_items_from_query(query_id)

    async def get_work_items_with_details(self, **kwargs) -> List[WorkItem]:
        return await self.client.get_work_items_from_query(
            query_id=self.query_id, **kwargs
        )

    def get_all_work_item_types(self) -> List[WorkItemType]:
        return self.client.get_all_work_item_types()

    def get_work_item_type(self, type_name: str) -> Optional[WorkItemType]:
        return self.client.get_work_item_type(type_name)

    @property
    def root_work_item_type(self) -> str:
        return self.client.root_work_item_type


class GitHubPlatformClient(PlatformClient):
    """This class provides a platform-specific client for GitHub."""

    def __init__(self, config: GitHubConfig):
        self.client = GitHubClient(config)

    async def initialize(self):
        await self.client.initialize()

    async def get_work_item_by_id(self, item_id: int) -> WorkItem:
        return await self.client.get_issue_by_number(item_id)

    async def get_work_items_from_query(self, query_id: str) -> List[WorkItem]:
        # GitHub doesn't use query_id, so we'll ignore it
        return await self.client.get_issues_from_query("")

    async def get_work_items_with_details(self, **kwargs) -> List[WorkItem]:
        return await self.client.get_issues_with_details(**kwargs)

    def get_all_work_item_types(self) -> List[WorkItemType]:
        return self.client.get_all_issue_types()

    def get_work_item_type(self, type_name: str) -> Optional[WorkItemType]:
        return self.client.get_issue_type(type_name)

    @property
    def root_work_item_type(self) -> str:
        return ""  # GitHub doesn't have a concept of root work item type


class Work:
    """This class provides a wrapper to abstract away the platform-specific details of fetching work items."""

    def __init__(self, config: Config):
        self.all: Dict[int, HierarchicalWorkItem] = {}
        self.root_items: List[HierarchicalWorkItem] = []
        self.by_type: List[WorkItemGroup[HierarchicalWorkItem]] = []
        self.root_type: str = ""

        self.platform = config.project.platform
        self.organization = config.project.platform.organization
        self.project = config.project.ref

        self.client = self._create_platform_client(config)

    def _create_platform_client(self, config: Config) -> PlatformClient:
        if self.platform.platform == Platform.AZURE_DEVOPS:
            client_config = DevOpsConfig(
                url=config.project.platform.base_url,
                org=self.organization,
                project=self.project,
                query=config.project.platform.query,
                pat=config.project.platform.access_token,
            )
            return DevOpsPlatformClient(client_config)
        elif self.platform.platform == Platform.GITHUB:
            client_config = GitHubConfig(
                access_token=config.project.platform.access_token,
                repo_name=config.project.ref,
            )
            return GitHubPlatformClient(client_config)
        else:
            raise ValueError(f"Unsupported platform: {self.platform}")

    async def initialize(self):
        """Initialize the client."""
        await self.client.initialize()
        self.root_type = self.client.root_work_item_type

    def add(self, work_item: WorkItem) -> Dict[int, HierarchicalWorkItem]:
        """Add a work item to the collection if it doesn't already exist."""
        if work_item.id not in self.all:
            hierarchical_item = self._convert_to_hierarchical(work_item)
            self.all[work_item.id] = hierarchical_item
        return self.all

    async def get_item_by_id(self, item_id: Union[int, str]) -> HierarchicalWorkItem:
        """Retrieve details for a specific work item."""
        item = await self.client.get_work_item_by_id(int(item_id))
        return self.add(item)[item.id]

    async def get_items_from_query(self, query_id: str) -> List[HierarchicalWorkItem]:
        """Retrieve work items based on a search query."""
        items = await self.client.get_work_items_from_query(query_id)
        for item in items:
            self.add(item)
        return self._build_hierarchy()

    async def get_items_with_details(self, **kwargs) -> List[HierarchicalWorkItem]:
        """Retrieve work items with details."""
        items = await self.client.get_work_items_with_details(**kwargs)
        for item in items:
            self.add(item)

        # Create a copy of the values to iterate over
        all_items = list(self.all.values())
        for item in all_items:
            await self._get_parent(item)

        self._create_other_parent()
        self._work_item_tree()

        self.by_type = self._group_by_type(self.root_items)

        return self._build_hierarchy()

    def get_work_item_types(self) -> List[WorkItemType]:
        """Get all work item types."""
        return self.client.get_all_work_item_types()

    def get_work_item_type(self, type_name: str) -> Optional[WorkItemType]:
        """Get a work item type by name."""
        return self.client.get_work_item_type(type_name)

    async def generate_ordered_work_items(
        self,
    ) -> List[WorkItemGroup["HierarchicalWorkItem"]]:
        """Generate an ordered list of work items grouped by type."""
        await self.get_items_with_details()
        return self.by_type

    def _remove_child_from_workitem(self, parent_id: int, child_id: int):
        """Remove a child from a parent work item."""
        parent_item = self.all.get(parent_id)
        if parent_item and parent_item.children:
            parent_item.children = [
                child for child in parent_item.children if child.id != child_id
            ]

    def _create_other_parent(self):
        """Create an 'Other' parent for orphaned items."""
        orphaned_items = [
            item for item in self.all.values() if item.orphan and item.id != 0
        ]

        if orphaned_items:
            log.info("Creating 'Other' work item for orphaned items")
            other_parent = HierarchicalWorkItem(
                type="Other",
                root=True,
                orphan=False,
                id=0,
                title="Other",
                state="Other",
                comment_count=0,
                parent_id=0,
                icon="https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_review?color=333333&v=2",
            )
            other_parent.children = orphaned_items
            other_parent.children_by_type = self._group_children_by_type(orphaned_items)
            self.all[0] = other_parent

            for item in orphaned_items:
                item.parent_id = 0
                item.orphan = False

    def _work_item_tree(self) -> None:
        """Build a tree structure of work items."""
        self.root_items = []
        other_parent = None

        all_items = list(self.all.values())
        for item in all_items:
            if item.id == 0:  # This is the "Other" parent
                other_parent = item
                continue

            if item.parent_id and item.parent_id in self.all and item.parent_id != 0:
                parent_item = self.all[item.parent_id]
                if item not in parent_item.children:
                    parent_item.children.append(item)
            elif item.root and not item.orphan:
                self.root_items.append(item)

        if other_parent:
            self.root_items.append(other_parent)

    def _group_by_type(
        self, items: List[HierarchicalWorkItem]
    ) -> List[WorkItemGroup[HierarchicalWorkItem]]:
        """Group work items by their type while preserving hierarchy."""
        grouped_items: Dict[str, List[HierarchicalWorkItem]] = {}
        for item in items:
            if item.type not in grouped_items:
                grouped_items[item.type] = []
            grouped_items[item.type].append(item)

        grouped_children_list = []
        for key, value in grouped_items.items():
            grouped_children_list.append(
                WorkItemGroup(item_type=key, icon=value[0].icon, items=value)
            )

        # Ensure "Other" group is at the end of the list
        other_group = next(
            (group for group in grouped_children_list if group.type == "Other"), None
        )
        if other_group:
            grouped_children_list.remove(other_group)
            grouped_children_list.append(other_group)

        return grouped_children_list

    async def _get_parent(self, item: HierarchicalWorkItem):
        """Recursively fetch parent work items and add them to the list asynchronously."""
        if item.parent_id and item.parent_id not in self.all:
            parent_item = await self.get_item_by_id(item.parent_id)
            await self._get_parent(parent_item)

    def _convert_to_hierarchical(self, item: WorkItem) -> HierarchicalWorkItem:
        """Convert a WorkItem to a HierarchicalWorkItem."""
        return HierarchicalWorkItem(**item.__dict__)

    def _build_hierarchy(self) -> List[HierarchicalWorkItem]:
        """Build a hierarchical structure from the flat list of work items."""
        root_items: List[HierarchicalWorkItem] = []
        processed_ids: Set[int] = set()

        def process_item(item: HierarchicalWorkItem):
            if item.id in processed_ids:
                return
            processed_ids.add(item.id)

            if item.parent_id and item.parent_id in self.all and item.parent_id != 0:
                parent = self.all[item.parent_id]
                if item not in parent.children:
                    parent.children.append(item)
                process_item(parent)
            elif item.id == 0 or (item.root and not item.orphan):
                if item not in root_items:
                    root_items.append(item)

            if item.id != 0:  # Skip processing children for "Other" parent
                for child in item.children:
                    process_item(child)

        all_items = list(self.all.values())
        for item in all_items:
            process_item(item)

        # Group children by type for root items (except "Other")
        for item in root_items:
            if item.id != 0:  # Skip "Other" parent
                item.children_by_type = self._group_children_by_type(item.children)

        return root_items

    def _group_children_by_type(
        self, children: List[HierarchicalWorkItem]
    ) -> List[WorkItemGroup[HierarchicalWorkItem]]:
        """Group children by their type."""
        type_groups: Dict[str, WorkItemGroup[HierarchicalWorkItem]] = {}
        for child in children:
            if child.type not in type_groups:
                type_groups[child.type] = WorkItemGroup(
                    item_type=child.type, icon=child.icon, items=[]
                )
            type_groups[child.type].items.append(child)
        return list(type_groups.values())
