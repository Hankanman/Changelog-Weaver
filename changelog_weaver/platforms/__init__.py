"""Platform implementations for changelog_weaver."""

from .devops import DevOpsConfig, DevOpsClient
from .github import GitHubConfig, GitHubClient

__all__ = [
    "DevOpsConfig",
    "DevOpsClient",
    "GitHubConfig",
    "GitHubClient",
]
