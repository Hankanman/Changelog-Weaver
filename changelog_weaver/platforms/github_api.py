"""GitHub API module for interacting with GitHub issues and pull requests."""

from typing import List, Optional, Dict, Union
from datetime import datetime
from github import Github
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository
from github.Commit import Commit
from ..utilities.utils import clean_string, format_date
from ..typings import WorkItem, WorkItemType, HierarchicalWorkItem, CommitInfo


class GitHubAPI:
    """Class for interacting with the GitHub API."""

    def __init__(self, config):
        """Initialize the GitHubAPI class."""
        self.config = config
        self.client: Github = config.client
        self.repo: Repository = self.client.get_repo(self.config.repo_name)
        self.issue_types: Dict[str, WorkItemType] = {}

    async def initialize(self):
        """Initialize the API by fetching issue types."""
        await self.fetch_issue_types()

    async def fetch_issue_types(self):
        """Fetch and store issue types from the repository."""
        labels = self.repo.get_labels()
        self.issue_types = {
            label.name: self._convert_label_to_work_item_type(label) for label in labels
        }
        self.issue_types["Other"] = WorkItemType(
            name="Other",
            icon="https://github.com/favicon.ico",
            color="#333333",
        )

    @staticmethod
    def _convert_label_to_work_item_type(label) -> WorkItemType:
        """Convert a GitHub label to a WorkItemType."""
        return WorkItemType(
            name=label.name,
            icon="https://github.com/favicon.ico",
            color=f"#{label.color}" if label.color else "#000000",
        )

    async def get_commits(
        self, since: Optional[str] = None, until: Optional[str] = None
    ) -> List[CommitInfo]:
        """Fetch commits from the repository within the specified date range."""
        since_dt: Optional[datetime] = datetime.fromisoformat(since) if since else None
        until_dt: Optional[datetime] = datetime.fromisoformat(until) if until else None
        kwargs = {}
        if since_dt:
            kwargs["since"] = since_dt
        if until_dt:
            kwargs["until"] = until_dt
        commits = self.repo.get_commits(**kwargs)
        return [await self._convert_to_commit_info(commit) for commit in commits]

    async def _convert_to_commit_info(self, commit: Commit) -> CommitInfo:
        """Convert a GitHub Commit object to a CommitInfo object."""
        return CommitInfo(
            sha=commit.sha,
            message=commit.commit.message.lower().split("\n")[
                0
            ],  # Only take the first line
            author=commit.commit.author.name,
            date=format_date(commit.commit.author.date),
            url=commit.html_url,
        )

    def get_issue_type(self, type_name: str) -> Optional[WorkItemType]:
        """Get the WorkItemType for a given type name."""
        return self.issue_types.get(type_name)

    def get_all_issue_types(self) -> List[WorkItemType]:
        """Get all WorkItemTypes."""
        return list(self.issue_types.values())

    async def get_issues_from_query(self, query: str) -> List[WorkItem]:
        """Get issues based on a query string."""
        issues_and_prs = self.client.search_issues(
            query=f"repo:{self.config.repo_name} {query}"
        )
        return [await self._convert_to_work_item(item) for item in issues_and_prs]

    async def get_issue_by_number(self, issue_number: int) -> WorkItem:
        """Get a specific issue by its number."""
        issue = self.repo.get_issue(number=issue_number)
        return await self._convert_to_work_item(issue)

    async def get_issues_with_details(
        self, state: str = "all", labels: Optional[List[str]] = None
    ) -> List[WorkItem]:
        """Get issues with additional details."""
        issues = self.repo.get_issues(state=state, labels=labels or [])
        return [await self._convert_to_work_item(issue) for issue in issues]

    async def get_pull_requests(self, state: str = "all") -> List[WorkItem]:
        """Get pull requests from the repository."""
        pull_requests = self.repo.get_pulls(
            state=state, sort="created", direction="desc"
        )
        return [await self._convert_to_work_item(pr) for pr in pull_requests]

    async def get_all_work_items(self, **kwargs) -> List[HierarchicalWorkItem]:
        """Get all work items including issues, pull requests, and commits."""
        issues = await self.get_issues_with_details(**kwargs)
        pull_requests = await self.get_pull_requests(**kwargs)
        commit_kwargs = {k: v for k, v in kwargs.items() if k in ["since", "until"]}
        commits = await self.get_commits(**commit_kwargs)

        issues_root = HierarchicalWorkItem(
            id=-1,
            type="Issue",
            state="N/A",
            title="Issue",
            icon="https://github.githubassets.com/images/modules/logos_page/Octocat.png",
            root=True,
            orphan=False,
            children=[
                HierarchicalWorkItem(**issue.__dict__)
                for issue in issues
                if not hasattr(issue, "pull_request")
            ],
        )

        prs_root = HierarchicalWorkItem(
            id=-2,
            type="Pull Request",
            state="N/A",
            title="Pull Request",
            icon="https://github.githubassets.com/images/modules/git-pull-request.svg",
            root=True,
            orphan=False,
            children=[HierarchicalWorkItem(**pr.__dict__) for pr in pull_requests],
        )

        commits_root = HierarchicalWorkItem(
            id=-3,
            type="Commit",
            state="N/A",
            title="Commit",
            icon="https://github.githubassets.com/images/modules/commits/commit.svg",
            root=True,
            orphan=False,
            children=[
                HierarchicalWorkItem(
                    id=(
                        int(commit.sha[:7], 16)
                        if commit.sha[:7].isalnum()
                        else hash(commit.sha[:7])
                    ),
                    type="Commit",
                    state="N/A",
                    title=commit.message,
                    icon="https://github.githubassets.com/images/modules/commits/commit.svg",
                    root=False,
                    orphan=True,
                    children=[],
                    url=commit.url,
                    sha=commit.sha[:7],
                )
                for commit in commits
            ],
        )

        return [issues_root, prs_root, commits_root]

    async def _convert_to_work_item(
        self, github_item: Union[Issue, PullRequest]
    ) -> WorkItem:
        """Convert a GitHub issue or pull request to a WorkItem."""
        item_type = (
            "PullRequest"
            if isinstance(github_item, PullRequest)
            or hasattr(github_item, "pull_request")
            else "Issue"
        )
        labels = [label.name for label in github_item.labels]
        primary_label = labels[0] if labels else "Other"
        issue_type_info = self.get_issue_type(primary_label)
        return WorkItem(
            id=github_item.number,
            root=False,
            orphan=True,
            title=clean_string(github_item.title, 1),
            state=github_item.state,
            type=item_type,
            icon=issue_type_info.icon if issue_type_info else "",
            comment_count=github_item.comments,
            description=clean_string(github_item.body or "", 10),
            tags=labels,
            url=github_item.html_url,
            comments=await self._get_comments(github_item),
        )

    async def _get_comments(self, github_item: Union[Issue, PullRequest]) -> List[str]:
        """Get comments for a GitHub issue or pull request."""
        return [
            f"{format_date(comment.created_at)} | {comment.user.login} | {clean_string(comment.body, 10)}"
            for comment in github_item.get_comments()
        ]
