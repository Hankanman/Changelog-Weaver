"""This module contains the GitHub platform client implementation."""

from typing import List, Optional
from dataclasses import dataclass, field
from github import Github

from .base import PlatformClient
from ..typings import WorkItem, WorkItemType
from .github_api import GitHubAPI


@dataclass
class GitHubConfig:
    """This class holds the configuration for the GitHub API and creates the connection."""

    access_token: str
    repo_name: str
    client: Github = field(init=False)

    def __post_init__(self):
        self.client = Github(self.access_token)


class GitHubPlatformClient(PlatformClient):
    """GitHub platform client implementation."""

    def __init__(self, config: GitHubConfig):
        self.config = config
        self.api = GitHubAPI(config)

    async def initialize(self):
        await self.api.initialize()

    async def close(self):
        """Close the API client."""
        # GitHub API doesn't require explicit closing, but we implement the method
        # to conform to the PlatformClient interface

    async def get_work_item_by_id(self, item_id: int) -> WorkItem:
        return await self.api.get_issue_by_number(item_id)

    async def get_work_items_from_query(self, query_id: str) -> List[WorkItem]:
        # GitHub doesn't use query_id, so we'll ignore it
        return await self.api.get_issues_from_query("")

    async def get_work_items_with_details(self, **kwargs) -> List[WorkItem]:
        return await self.api.get_issues_with_details(**kwargs)

    def get_all_work_item_types(self) -> List[WorkItemType]:
        return self.api.get_all_issue_types()

    def get_work_item_type(self, type_name: str) -> Optional[WorkItemType]:
        return self.api.get_issue_type(type_name)

    @property
    def root_work_item_type(self) -> str:
        return ""  # GitHub doesn't have a concept of root work item type
