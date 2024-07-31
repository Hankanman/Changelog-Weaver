"""Work module for changelog-weaver"""

from typing import Dict, List, Union, Optional, Set
import asyncio
import time
import logging as log
from .configuration import Config
from .typings import (
    HierarchicalWorkItem,
    WorkItemGroup,
    Platform,
    WorkItem,
    WorkItemType,
)
from .platforms import (
    PlatformClient,
    DevOpsPlatformClient,
    GitHubPlatformClient,
    DevOpsConfig,
    GitHubConfig,
)
from .utilities import Hierarchy


class Work:
    """Work class for handling work items."""

    def __init__(self, config: Config):
        self.all: Dict[int, HierarchicalWorkItem] = {}
        self.root_items: List[HierarchicalWorkItem] = []
        self.by_type: List[WorkItemGroup] = []
        self.platform = config.project.platform
        self.client = self._create_platform_client(config)

    def _create_platform_client(self, config: Config) -> PlatformClient:
        """Create the platform client based on the configuration."""
        if self.platform.platform == Platform.AZURE_DEVOPS:
            return DevOpsPlatformClient(
                DevOpsConfig(
                    url=config.project.platform.base_url,
                    org=config.project.platform.organization,
                    project=config.project.ref,
                    query=config.project.platform.query,
                    pat=config.project.platform.access_token,
                )
            )
        elif self.platform.platform == Platform.GITHUB:
            return GitHubPlatformClient(
                GitHubConfig(
                    access_token=config.project.platform.access_token,
                    repo_name=config.project.ref,
                )
            )
        else:
            raise ValueError(f"Unsupported platform: {self.platform}")

    async def initialize(self):
        """Initialize the client session."""
        log.info("Initializing Work class")
        start_time = time.time()
        await self.client.initialize()
        end_time = time.time()
        log.info(f"Work class initialized in {end_time - start_time} seconds")

    async def close(self):
        """Close the client session."""
        if hasattr(self.client, "close"):
            await self.client.close()

    def add(self, work_item: WorkItem) -> HierarchicalWorkItem:
        """Add a work item to the collection."""
        if work_item.id not in self.all:
            hierarchical_item = HierarchicalWorkItem(**work_item.__dict__)
            self.all[work_item.id] = hierarchical_item
        return self.all[work_item.id]

    async def get_item_by_id(self, item_id: Union[int, str]) -> HierarchicalWorkItem:
        """Get a work item by its ID."""
        item = await self.client.get_work_item_by_id(int(item_id))
        return self.add(item)

    async def get_items_from_query(self, query_id: str) -> List[HierarchicalWorkItem]:
        """Get work items from a query."""
        items = await self.client.get_work_items_from_query(query_id)
        return [self.add(item) for item in items]

    async def get_items_with_details(self, **kwargs) -> List[HierarchicalWorkItem]:
        """Get work items with details."""
        log.info("Starting to fetch work items with details")
        start_time = time.time()

        items = await self.client.get_work_items_with_details(**kwargs)
        log.info("Fetched %s work items from client", len(items))

        add_tasks = [self.get_item_by_id(item.id) for item in items]
        await asyncio.gather(*add_tasks)
        log.info("Added %s items to the work item collection", len(add_tasks))

        await self._fetch_parents()
        log.info("Fetched parent items")

        self._create_other_parent()
        log.info("Created 'Other' parent for orphaned items")

        hierarchy = Hierarchy(self.all)
        self.root_items = hierarchy.root_items
        self.by_type = hierarchy.by_type

        end_time = time.time()
        log.info(
            "Fetched and processed work items in %.2f seconds", end_time - start_time
        )

        return self.root_items

    async def _fetch_parents(self):
        """Fetch parent items for all work items."""
        log.info("Starting to fetch parent items")
        start_time = time.time()
        items_to_fetch = set()

        # Create a list of items to avoid modifying the dictionary during iteration
        items_list = list(self.all.values())

        for item in items_list:
            current_item = item
            while current_item.parent_id and current_item.parent_id not in self.all:
                items_to_fetch.add(current_item.parent_id)
                current_item = await self.get_item_by_id(current_item.parent_id)

        log.info(f"Fetching {len(items_to_fetch)} parent items")

        # Fetch parent items in batches
        batch_size = 10
        for i in range(0, len(items_to_fetch), batch_size):
            batch = list(items_to_fetch)[i : i + batch_size]
            parent_fetch_tasks = [self.get_item_by_id(parent_id) for parent_id in batch]
            await asyncio.gather(*parent_fetch_tasks)

        end_time = time.time()
        log.info(f"Fetched parent items in {end_time - start_time:.2f} seconds")

    async def _fetch_parent_chain(
        self, item: HierarchicalWorkItem, items_to_fetch: Set[int]
    ):
        """Fetch the parent chain for a work item."""
        current_item = item
        while current_item.parent_id and current_item.parent_id not in self.all:
            items_to_fetch.add(current_item.parent_id)
            parent = await self.get_item_by_id(current_item.parent_id)
            current_item = parent

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
            self.all[0] = other_parent
            for item in orphaned_items:
                item.parent_id = 0

    async def generate_ordered_work_items(self) -> List[WorkItemGroup]:
        """Generate ordered work items."""
        log.info("Generating ordered work items")
        start_time = time.time()

        if not self.by_type:  # Only fetch items if we haven't already
            await self.get_items_with_details()

        end_time = time.time()
        log.info(f"Generated ordered work items in {end_time - start_time:.2f} seconds")
        return self.by_type

    def get_work_item_types(self) -> List[WorkItemType]:
        """Get all work item types."""
        return self.client.get_all_work_item_types()

    def get_work_item_type(self, type_name: str) -> Optional[WorkItemType]:
        """Get the work item type by name."""
        return self.client.get_work_item_type(type_name)
