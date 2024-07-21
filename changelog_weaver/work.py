"""This module provides a wrapper class to abstract away the platform-specific details of fetching work items."""

from typing import List, Union, Dict, Optional

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

    async def get_items_from_query(self, query: str) -> List[HierarchicalWorkItem]:
        """Retrieve work items based on a search query."""
        if self.devops:
            items = await self.devops.get_work_items_from_wiql(query)
        elif self.github:
            items = await self.github.get_issues_from_query(query)
        else:
            items = []
        return self._build_hierarchy(items)

    async def get_item_by_id(self, item_id: Union[int, str]) -> HierarchicalWorkItem:
        """Retrieve details for a specific work item."""
        if self.devops:
            item = await self.devops.get_work_item_by_id(int(item_id))
        elif self.github:
            item = await self.github.get_issue_by_number(int(item_id))
        else:
            item = WorkItem(id=0, title="", state="")
        return self._convert_to_hierarchical(item)

    async def get_items_with_details(self, **kwargs) -> List[HierarchicalWorkItem]:
        """Retrieve work items with details."""
        if self.devops:
            items = await self.devops.get_work_items_from_query(**kwargs)
        elif self.github:
            items = await self.github.get_issues_with_details(**kwargs)
        else:
            items = []
        return self._build_hierarchy(items)

    def _convert_to_hierarchical(self, item: WorkItem) -> HierarchicalWorkItem:
        """Convert a WorkItem to a HierarchicalWorkItem."""
        return HierarchicalWorkItem(**item.__dict__)

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
            if item.parent and item.parent in item_map:
                item_map[item.parent].children.append(item)
            else:
                root_items.append(item)

        # Third pass: group children by type
        for item in item_map.values():
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

    def get_work_item_types(self) -> List[WorkItemType]:
        """Get all work item types."""
        if self.devops:
            return self.devops.get_all_work_item_types()
        elif self.github:
            return self.github.get_all_issue_types()
        return []

    def get_work_item_type(self, type_name: str) -> Optional[WorkItemType]:
        """Get a work item type by name."""
        if self.devops:
            return self.devops.get_work_item_type(type_name)
        elif self.github:
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
