"""
Git service adapters package.

This package contains implementations of Git service adapters for different
hosting platforms (GitHub, Forgejo, etc.).
"""

from .base_adapter import BaseGitAdapter, GitOperationResult
from .github_adapter import GitHubAdapter
from .forgejo_adapter import ForgejoAdapter

__all__ = [
    "BaseGitAdapter",
    "GitOperationResult",
    "GitHubAdapter",
    "ForgejoAdapter",
]
