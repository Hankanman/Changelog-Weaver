""" Base class for platform clients. """

from abc import ABC, abstractmethod
from typing import List, Optional
from ..typings import WorkItem, WorkItemType, CommitInfo


class PlatformClient(ABC):
    """Base class for platform clients."""

    @abstractmethod
    async def initialize(self):
        """Initialize the API client."""

    @abstractmethod
    async def close(self):
        """Close the API client."""

    @abstractmethod
    async def get_work_item_by_id(self, item_id: int) -> WorkItem:
        """Get a work item by its ID."""

    @abstractmethod
    async def get_work_items_from_query(self, query_id: str) -> List[WorkItem]:
        """Get work items from a query."""

    @abstractmethod
    async def get_work_items_with_details(self, **kwargs) -> List[WorkItem]:
        """Get work items with details."""

    @abstractmethod
    def get_all_work_item_types(self) -> List[WorkItemType]:
        """Get all work item types."""

    @abstractmethod
    def get_work_item_type(self, type_name: str) -> Optional[WorkItemType]:
        """Get a work item type by name."""

    @abstractmethod
    async def get_commits(self, **kwargs) -> List[CommitInfo]:
        """Get commits from the repository."""

    @property
    @abstractmethod
    def root_work_item_type(self) -> str:
        """Get the root work item type."""
