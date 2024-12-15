"""GitHub API module for interacting with GitHub issues and pull requests."""

from typing import List, Optional, Dict, Union, Tuple
from datetime import datetime
from github import Github
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository
from github.Commit import Commit
from ..utilities.utils import clean_string, format_date
from ..typings import WorkItem, WorkItemType, HierarchicalWorkItem, CommitInfo
from ..logger import get_logger

log = get_logger(__name__)


class GitHubAPI:
    """Class for interacting with the GitHub API."""

    def __init__(self, config):
        """Initialize the GitHubAPI class."""
        self.config = config
        self.client: Github = config.client
        self.repo: Repository = self.client.get_repo(self.config.repo_name)
        self.branch: Optional[str] = config.branch
        self.from_tag: Optional[str] = config.from_tag
        self.to_tag: Optional[str] = config.to_tag
        log.info(
            f"GitHubAPI initialized with branch: {self.branch}, "
            f"from_tag: {self.from_tag}, to_tag: {self.to_tag}"
        )
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
        self,
        since: Optional[str] = None,
        until: Optional[str] = None,
        from_tag: Optional[str] = None,
        to_tag: Optional[str] = None,
    ) -> List[CommitInfo]:
        """
        Fetch commits from the repository within the specified date range and/or between tags.
        """
        # Build kwargs for get_commits
        kwargs = {}
        if since:
            kwargs["since"] = datetime.fromisoformat(since)
        if until:
            kwargs["until"] = datetime.fromisoformat(until)

        # Use the configured branch if available
        branch = self.branch or "main"
        kwargs["sha"] = branch

        log.info(f"Fetching commits from branch: {branch}")
        if from_tag and to_tag:
            log.info(f"Filtering commits between tags: {from_tag} and {to_tag}")

            try:
                # Fetch all tags
                tags = self.repo.get_tags()
                tag_dict = {tag.name: tag.commit.sha for tag in tags}

                # Get commit SHAs for the tags
                from_commit = tag_dict.get(from_tag)
                to_commit = tag_dict.get(to_tag)

                if not from_commit or not to_commit:
                    missing_tag = from_tag if not from_commit else to_tag
                    log.error(f"Tag not found: {missing_tag}")
                    return []

                log.info(f"From commit SHA: {from_commit}")
                log.info(f"To commit SHA: {to_commit}")

                # Get the comparison
                comparison = self.repo.compare(from_commit, to_commit)

                log.info(f"Found {comparison.total_commits} commits between tags")

                # No need to filter by branch as comparison is between specified commits
                commits_list = list(comparison.commits)
                # Reverse the commits list to have the most recent commits first
                commits_list.reverse()
                return [
                    await self._convert_to_commit_info(commit)
                    for commit in commits_list
                ]

            except Exception as e:
                log.error(f"Error filtering commits by tags: {str(e)}")
                return []

        # If no tags specified or tag filtering failed, get commits normally
        commits = self.repo.get_commits(**kwargs)
        return [await self._convert_to_commit_info(commit) for commit in commits]

    async def _get_commit_range(
        self, from_tag: Optional[str], to_tag: Optional[str]
    ) -> Optional[Tuple[str, str]]:
        """
        Get the commit range between two tags.

        Args:
            from_tag (Optional[str]): The starting tag.
            to_tag (Optional[str]): The ending tag.

        Returns:
            Optional[Tuple[str, str]]: A tuple of (from_commit_sha, to_commit_sha) or None if tags not specified.
        """
        if not (from_tag and to_tag):
            return None

        try:
            from_ref = self.repo.get_git_ref(f"tags/{from_tag}")
            to_ref = self.repo.get_git_ref(f"tags/{to_tag}")

            # Get the commit SHA for each tag
            from_sha = from_ref.object.sha
            to_sha = to_ref.object.sha

            return (from_sha, to_sha)
        except Exception as e:
            log.warning(
                f"Error getting commit range for tags {from_tag} to {to_tag}: {str(e)}"
            )
            return None

    def _is_commit_in_range(self, commit_sha: str, from_sha: str, to_sha: str) -> bool:
        """
        Check if a commit is within the specified range.

        Args:
            commit_sha (str): The SHA of the commit to check.
            from_sha (str): The starting commit SHA.
            to_sha (str): The ending commit SHA.

        Returns:
            bool: True if the commit is in range, False otherwise.
        """
        try:
            # Get the comparison between the commits
            comparison = self.repo.compare(from_sha, to_sha)

            # Check if the commit is in the comparison's commits
            commit_shas = [commit.sha for commit in comparison.commits]
            return commit_sha in commit_shas
        except Exception as e:
            log.warning(f"Error checking commit range for {commit_sha}: {str(e)}")
            return False

    async def _convert_to_commit_info(self, commit: Commit) -> CommitInfo:
        """
        Convert a GitHub Commit object to a CommitInfo object.

        Args:
            commit (Commit): The GitHub Commit object to convert.

        Returns:
            CommitInfo: The converted CommitInfo object.
        """
        return CommitInfo(
            sha=str(commit.sha),  # Explicitly convert to string
            message=commit.commit.message.split("\n")[0],  # Only take the first line
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
        """Get all work items including issues and pull requests."""
        issues = await self.get_issues_with_details(**kwargs)
        pull_requests = await self.get_pull_requests(**kwargs)

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

        return [issues_root, prs_root]

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
