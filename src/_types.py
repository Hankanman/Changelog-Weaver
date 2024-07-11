"""This module contains classes for representing work items, users, and comments."""

from typing import List, Optional
from dataclasses import dataclass, field

from src.utils import clean_string, format_date, clean_name


@dataclass
class WorkItemChildren:
    """Represents a work item's children."""

    type: str
    items: List["WorkItem"]
    icon: str = ""


@dataclass
# pylint: disable=too-many-instance-attributes
class WorkItem:
    """Represents a work item."""

    id: int
    title: str
    state: str
    type: str = ""
    comment_count: int = field(default=0, metadata={"alias": "commentCount"})
    parent: int = 0
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
    children: List["WorkItem"] = field(default_factory=list)
    children_by_type: List[WorkItemChildren] = field(default_factory=list)


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
        self.text = clean_string(text)
        self.modified_date = format_date(modified_date)
        self.modified_by = modified_by
