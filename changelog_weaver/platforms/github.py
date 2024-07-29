"""This module contains the GitHub configuration and API interaction classes."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from github import Github, GithubException
from github.Repository import Repository
from github.Label import Label

from ..utilities.utils import clean_string

from ..typings.types import WorkItem, WorkItemType


@dataclass
class GitHubConfig:
    """This class holds the configuration for the GitHub API and creates the connection."""

    access_token: str
    repo_name: str
    client: Github = field(init=False)

    def __post_init__(self):
        self.client = Github(self.access_token)


class GitHubClient:
    """This class provides methods to interact with GitHub API."""

    def __init__(self, config: GitHubConfig):
        self.config = config
        self.repo: Repository = self.config.client.get_repo(self.config.repo_name)
        self.issue_types: Dict[str, WorkItemType] = {}

    async def initialize(self):
        """Initialize the client by fetching issue types (labels)."""
        await self.fetch_issue_types()

    async def fetch_issue_types(self):
        """Fetch issue types (labels) and store them in the client."""
        labels = self.repo.get_labels()
        self.issue_types = {
            label.name: self._convert_label_to_work_item_type(label) for label in labels
        }
        # Add a default "Other" type
        self.issue_types["Other"] = WorkItemType(
            name="Other",
            icon="https://github.com/favicon.ico",  # Using GitHub favicon as a default icon
            color="#333333",
        )

    @staticmethod
    def _convert_label_to_work_item_type(label: Label) -> WorkItemType:
        """Convert a GitHub Label to our WorkItemType model."""
        return WorkItemType(
            name=label.name,
            icon="https://github.com/favicon.ico",  # Using GitHub favicon as we don't have specific icons for labels
            color=f"#{label.color}" if label.color else "#000000",
        )

    def get_issue_type(self, type_name: str) -> Optional[WorkItemType]:
        """Get an issue type (label) by name."""
        return self.issue_types.get(type_name)

    def get_all_issue_types(self) -> List[WorkItemType]:
        """Get all issue types (labels)."""
        return list(self.issue_types.values())

    async def get_issues_from_query(self, query: str) -> List[WorkItem]:
        """Retrieve issues based on a search query.

        The query should be formatted according to GitHub's search syntax.
        For example: 'repo:owner/repo is:issue is:open label:bug'
        """
        try:
            # Ensure the query includes the correct repository
            if f"repo:{self.config.repo_name}" not in query:
                query = f"repo:{self.config.repo_name} {query}"
            issues_and_prs = self.config.client.search_issues(query=query)
            return [self._convert_to_work_item(item) for item in issues_and_prs]
        except GithubException as e:
            print(f"Error searching for issues: {e}")
            return []

    async def get_issue_by_number(self, issue_number: int) -> WorkItem:
        """Retrieve details for a specific issue."""
        try:
            issue = self.repo.get_issue(number=issue_number)
            return self._convert_to_work_item(issue)
        except GithubException:
            return WorkItem(
                id=0,
                title="",
                state="",
                type="Issue",
                icon="",
                root=False,
                orphan=False,
            )

    async def get_issues_with_details(
        self, state: str = "all", labels: Optional[List[str]] = None
    ) -> List[WorkItem]:
        """Retrieve issues with details."""
        issues = self.repo.get_issues(state=state, labels=labels or [])
        return [self._convert_to_work_item(issue) for issue in issues]

    async def get_pull_requests(self, state: str = "all") -> List[WorkItem]:
        """Retrieve pull requests."""
        pull_requests = self.repo.get_pulls(
            state=state, sort="created", direction="desc"
        )
        return [self._convert_to_work_item(pr) for pr in pull_requests]

    def _convert_to_work_item(self, github_item) -> WorkItem:
        """Convert GitHub Issue or PullRequest to our WorkItem type."""
        item_type = "PullRequest" if github_item.pull_request else "Issue"
        labels = [label.name for label in github_item.labels]
        primary_label = labels[0] if labels else "Other"
        issue_type_info = self.get_issue_type(primary_label)

        return WorkItem(
            id=github_item.number,
            root=False,
            orphan=False,
            title=clean_string(github_item.title, 1),
            state=github_item.state,
            type=item_type,
            icon=issue_type_info.icon if issue_type_info else "",
            comment_count=github_item.comments,
            description=clean_string(github_item.body, 10),
            tags=labels,
            url=github_item.html_url,
            comments=self._get_comments(github_item),
        )

    def _get_comments(self, github_item) -> List[str]:
        """Retrieve comments for a GitHub item."""
        return [
            f"{comment.created_at} | {comment.user.login} | {clean_string(comment.body,10)}"
            for comment in github_item.get_comments()
        ]
