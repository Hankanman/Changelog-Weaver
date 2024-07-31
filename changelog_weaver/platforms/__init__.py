"""Platform implementations for changelog_weaver."""

from .base import PlatformClient
from .devops_client import DevOpsConfig, DevOpsPlatformClient
from .github_client import GitHubConfig, GitHubPlatformClient

__all__ = [
    "PlatformClient",
    "DevOpsConfig",
    "DevOpsPlatformClient",
    "GitHubConfig",
    "GitHubPlatformClient",
]
