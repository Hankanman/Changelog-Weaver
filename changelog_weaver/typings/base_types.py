""" Base types for the changelog_weaver package. """

from typing import List, Optional
from enum import Enum
from dataclasses import dataclass, field


@dataclass
class ApiDetails:
    """Configuration class for the API details."""

    key: str
    url: str
    model_name: str


@dataclass
class CommitInfo:
    """Dataclass for commit information"""

    sha: str
    message: str
    author: str
    date: str
    url: str


class Platform(Enum):
    """Enum for supported platforms"""

    AZURE_DEVOPS = "azure_devops"
    GITHUB = "github"


@dataclass
class WorkItemType:
    """Dataclass for work item types"""

    name: str
    icon: str
    color: str = "#000000"


# pylint: disable=too-many-instance-attributes
@dataclass
class WorkItem:
    """Dataclass for work items"""

    id: int
    type: str
    state: str
    title: str
    icon: str
    root: bool
    orphan: bool
    parent_id: int = 0
    parent: Optional["WorkItem"] = None
    comment_count: int = 0
    story_points: Optional[int] = None
    summary: Optional[str] = None
    priority: Optional[int] = None
    description: Optional[str] = None
    repro_steps: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    url: str = ""
    sha: Optional[str] = None
    comments: List[str] = field(default_factory=list)
