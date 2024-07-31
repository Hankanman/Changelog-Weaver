from typing import Dict, List, Union, Optional, Set
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
import logging as log
from .utilities import Hierarchy


class Work:
    def __init__(self, config: Config):
        self.all: Dict[int, HierarchicalWorkItem] = {}
        self.root_items: List[HierarchicalWorkItem] = []
        self.by_type: List[WorkItemGroup] = []
        self.platform = config.project.platform
        self.client = self._create_platform_client(config)

    def _create_platform_client(self, config: Config) -> PlatformClient:
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
        await self.client.initialize()

    def add(self, work_item: WorkItem) -> HierarchicalWorkItem:
        if work_item.id not in self.all:
            hierarchical_item = HierarchicalWorkItem(**work_item.__dict__)
            self.all[work_item.id] = hierarchical_item
        return self.all[work_item.id]

    async def get_item_by_id(self, item_id: Union[int, str]) -> HierarchicalWorkItem:
        item = await self.client.get_work_item_by_id(int(item_id))
        return self.add(item)

    async def get_items_from_query(self, query_id: str) -> List[HierarchicalWorkItem]:
        items = await self.client.get_work_items_from_query(query_id)
        return [self.add(item) for item in items]

    async def get_items_with_details(self, **kwargs) -> List[HierarchicalWorkItem]:
        items = await self.client.get_work_items_with_details(**kwargs)
        for item in items:
            self.add(item)
        await self._fetch_parents()
        self._create_other_parent()
        hierarchy = Hierarchy(self.all)
        self.root_items = hierarchy.root_items
        self.by_type = hierarchy.by_type
        return self.root_items

    async def _fetch_parents(self):
        items_to_fetch = set()
        for item in list(self.all.values()):  # Create a list from the dictionary values
            await self._fetch_parent_chain(item, items_to_fetch)

        for parent_id in items_to_fetch:
            await self.get_item_by_id(parent_id)

    async def _fetch_parent_chain(
        self, item: HierarchicalWorkItem, items_to_fetch: Set[int]
    ):
        current_item = item
        while current_item.parent_id and current_item.parent_id not in self.all:
            items_to_fetch.add(current_item.parent_id)
            parent = await self.get_item_by_id(current_item.parent_id)
            current_item = parent

    def _create_other_parent(self):
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
        await self.get_items_with_details()
        return self.by_type

    def get_work_item_types(self) -> List[WorkItemType]:
        return self.client.get_all_work_item_types()

    def get_work_item_type(self, type_name: str) -> Optional[WorkItemType]:
        return self.client.get_work_item_type(type_name)
