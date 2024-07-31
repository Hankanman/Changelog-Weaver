from typing import List, TypeVar, Generic
from dataclasses import dataclass, field

from .base_types import WorkItem, Platform


@dataclass
class HierarchicalWorkItem(WorkItem):
    children: List["HierarchicalWorkItem"] = field(default_factory=list)
    children_by_type: List["WorkItemGroup"] = field(default_factory=list)


@dataclass
class PlatformInfo:
    platform: Platform
    organization: str
    base_url: str
    query: str
    access_token: str


@dataclass
class Notes:
    notes: str = ""
    headers: List[str] = field(default_factory=list)


@dataclass
class Project:
    name: str
    ref: str
    url: str
    version: str
    brief: str
    platform: PlatformInfo
    changelog: Notes


T = TypeVar("T", WorkItem, "HierarchicalWorkItem")


# pylint: disable=redefined-builtin
class WorkItemGroup(Generic[T]):
    """Represents a group of work items."""

    def __init__(self, type: str, icon: str, items: List[T]):
        self.type = type
        self.icon = icon
        self.items: List[T] = items
