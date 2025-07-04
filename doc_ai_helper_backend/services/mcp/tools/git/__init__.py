"""
Git tools package for MCP integration.

This package provides a context-driven Git operations abstraction that supports
multiple Git hosting services (GitHub, Forgejo, etc.) through a unified interface.

The architecture consists of:
- Context: Repository context models and credential management
- Adapters: Service-specific implementations (GitHub, Forgejo, etc.)
- Operations: High-level operations (issues, PRs, repository management)
- Tools: Unified interface for MCP registration
- Service Resolver: Automatic service selection based on context

Usage:
    from doc_ai_helper_backend.services.mcp.tools.git import unified_git_tools

    # Create an issue using repository context
    result = await unified_git_tools.create_issue(
        repository_context="owner/repo",  # or detailed context dict
        title="Bug report",
        description="Description of the bug"
    )
"""

from .context import RepositoryContext, GitServiceType, CredentialManager
from .service_resolver import GitServiceResolver, resolve_git_adapter
from .adapters import BaseGitAdapter, GitOperationResult, GitHubAdapter, ForgejoAdapter
from .operations import IssueOperations, PROperations, RepositoryOperations
from .tools import UnifiedGitTools, unified_git_tools

__all__ = [
    # Context management
    "RepositoryContext",
    "GitServiceType",
    "CredentialManager",
    # Service resolution
    "GitServiceResolver",
    "resolve_git_adapter",
    # Adapters
    "BaseGitAdapter",
    "GitOperationResult",
    "GitHubAdapter",
    "ForgejoAdapter",
    # Operations
    "IssueOperations",
    "PROperations",
    "RepositoryOperations",
    # Unified tools (main interface)
    "UnifiedGitTools",
    "unified_git_tools",
]
