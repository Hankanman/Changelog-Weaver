"""This module contains the DevOps platform client implementation."""

from typing import List, Optional
from dataclasses import dataclass, field
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

from .platform_client import PlatformClient
from ..typings import WorkItem, WorkItemType, CommitInfo
from .devops_api import DevOpsAPI, FIELDS


# pylint: disable=too-many-instance-attributes
@dataclass
class DevOpsConfig:
    """Configuration class for the Azure DevOps platform."""

    url: str
    org: str
    project: str
    query: str
    pat: str
    repo_name: str
    fields: List[str] = field(default_factory=lambda: FIELDS)
    connection: Connection = field(init=False)

    def __post_init__(self):
        credentials = BasicAuthentication("", self.pat)
        self.connection = Connection(
            base_url=f"{self.url}/{self.org}", creds=credentials
        )


class DevOpsPlatformClient(PlatformClient):
    """Azure DevOps platform client class."""

    def __init__(self, config: DevOpsConfig):
        self.config = config
        self.api = DevOpsAPI(config)
        self.query_id = config.query

    async def initialize(self):
        await self.api.initialize()

    async def close(self):
        """Close the API client."""
        await self.api.close()

    async def get_work_item_by_id(self, item_id: int) -> WorkItem:
        return await self.api.get_work_item_by_id(item_id)

    async def get_work_items_from_query(self, query_id: str) -> List[WorkItem]:
        return await self.api.get_work_items_from_query(query_id)

    async def get_work_items_with_details(self, **kwargs) -> List[WorkItem]:
        return await self.api.get_work_items_from_query(
            query_id=self.query_id, **kwargs
        )

    def get_all_work_item_types(self) -> List[WorkItemType]:
        return self.api.get_all_work_item_types()

    def get_work_item_type(self, type_name: str) -> Optional[WorkItemType]:
        return self.api.get_work_item_type(type_name)

    async def get_commits(self, **kwargs) -> List[CommitInfo]:
        return await self.api.get_commits(**kwargs)

    @property
    def root_work_item_type(self) -> str:
        return self.api.root_work_item_type
