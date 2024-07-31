from abc import ABC, abstractmethod
from typing import List, Optional
from ..typings import WorkItem, WorkItemType


class PlatformClient(ABC):
    @abstractmethod
    async def initialize(self):
        pass

    @abstractmethod
    async def get_work_item_by_id(self, item_id: int) -> WorkItem:
        pass

    @abstractmethod
    async def get_work_items_from_query(self, query_id: str) -> List[WorkItem]:
        pass

    @abstractmethod
    async def get_work_items_with_details(self, **kwargs) -> List[WorkItem]:
        pass

    @abstractmethod
    def get_all_work_item_types(self) -> List[WorkItemType]:
        pass

    @abstractmethod
    def get_work_item_type(self, type_name: str) -> Optional[WorkItemType]:
        pass

    @property
    @abstractmethod
    def root_work_item_type(self) -> str:
        pass
