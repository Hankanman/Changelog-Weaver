"""This module contains classes for representing work items, users, and comments."""

from typing import List, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum

from ..utilities import clean_string, format_date, clean_name


class Platform(Enum):
    """Enum for supported platforms."""

    AZURE_DEVOPS = "azure_devops"
    GITHUB = "github"


@dataclass
class Notes:
    """Represents the notes for a software package."""

    notes: str = ""
    headers: List[str] = field(default_factory=list)

    def add_note(self, value: str):
        """Add notes to the software package.

        Args:
            value (str): The notes to add."""
        self.notes += value
        return self.notes

    def add_header(self, value: str):
        """Add a header to the software package.

        Args:
            value (str): The header to add."""
        self.headers.append(value)
        return self.headers


@dataclass
class PlatformInfo:
    """Represents the platform information"""

    platform: Platform
    organization: str
    base_url: str
    query: str
    access_token: str


@dataclass
class Project:
    """Represents a platform."""

    name: str
    ref: str
    url: str
    version: str
    brief: str
    platform: PlatformInfo
    changelog: Notes


@dataclass
# pylint: disable=too-many-instance-attributes
class WorkItem:
    """Represents a work item."""

    type: str
    root: bool
    orphan: bool
    id: int
    title: str
    state: str
    comment_count: int = field(default=0, metadata={"alias": "commentCount"})
    parent_id: int = field(default=0, metadata={"alias": "parent"})
    parent: Optional["WorkItem"] = None
    story_points: Optional[int] = field(default=None, metadata={"alias": "storyPoints"})
    priority: Optional[int] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    repro_steps: Optional[str] = field(default=None, metadata={"alias": "reproSteps"})
    acceptance_criteria: Optional[str] = field(
        default=None, metadata={"alias": "acceptanceCriteria"}
    )
    tags: List[str] = field(default_factory=list)
    url: str = ""
    comments: List[str] = field(default_factory=list)
    icon: str = ""

    children: List["HierarchicalWorkItem"] = field(default_factory=list)
    children_by_type: List["WorkItemGroup"] = field(default_factory=list)


T = TypeVar("T", WorkItem, "HierarchicalWorkItem")


@dataclass
class WorkItemGroup(Generic[T]):
    """Represents a group of work items."""

    def __init__(self, item_type: str, icon: str, items: List[T]):
        self.item_type = item_type
        self.icon = icon
        self.items: List[T] = items


@dataclass
class HierarchicalWorkItem(WorkItem):
    """Represents a hierarchical work item."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.children: List["HierarchicalWorkItem"] = []
        self.children_by_type: List[WorkItemGroup["HierarchicalWorkItem"]] = []


@dataclass
class WorkItemType:
    """Represents a work item type."""

    name: str
    icon: str
    color: str = "#000000"


@dataclass
class User:
    """Represents a user."""

    display_name: str
    url: str
    user_id: str
    unique_name: str

    def __init__(self, display_name: str, url: str, user_id: str, unique_name: str):
        self.display_name = clean_name(display_name)
        self.url = url
        self.user_id = user_id
        self.unique_name = unique_name


@dataclass
class Comment:
    """Represents a comment on a work item."""

    text: str
    modified_date: str
    modified_by: User

    def __init__(self, text: str, modified_date: str, modified_by: User):
        self.text = clean_string(text, 10)
        self.modified_date = format_date(modified_date)
        self.modified_by = modified_by
