"""
Git operations package.

This package contains high-level Git operations that work across different
Git service adapters, providing a unified interface for common Git tasks.
"""

from .issue_operations import IssueOperations
from .pr_operations import PROperations
from .repository_operations import RepositoryOperations

__all__ = [
    "IssueOperations",
    "PROperations", 
    "RepositoryOperations",
]
