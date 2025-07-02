"""
Base class for MCP Git tools abstraction.

This module provides the abstract base class for all Git service MCP tools,
defining the common interface for issue creation, pull request creation,
and repository operations across different Git hosting platforms.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .....models.repository_context import RepositoryContext

logger = logging.getLogger(__name__)


class MCPGitClientBase(ABC):
    """Abstract base class for Git API clients used by MCP tools."""

    def __init__(self, **kwargs):
        """Initialize the Git client with platform-specific configuration."""
        self.config = kwargs

    @abstractmethod
    async def create_issue(
        self,
        repository: str,
        title: str,
        description: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create an issue in the repository."""
        pass

    @abstractmethod
    async def create_pull_request(
        self,
        repository: str,
        title: str,
        description: str,
        head_branch: str,
        base_branch: str = "main",
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a pull request in the repository."""
        pass

    @abstractmethod
    async def check_repository_permissions(
        self, repository: str, **kwargs
    ) -> Dict[str, Any]:
        """Check permissions for a repository."""
        pass


class MCPGitToolsBase(ABC):
    """Abstract base class for MCP Git tools."""

    def __init__(self, client: MCPGitClientBase):
        """Initialize with a Git client."""
        self.client = client

    async def create_issue(
        self,
        title: str,
        description: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        repository_context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> str:
        """
        Create an issue in the repository with context validation.

        Args:
            title: Issue title
            description: Issue description
            labels: Issue labels
            assignees: Issue assignees
            repository_context: Current repository context
            **kwargs: Additional platform-specific parameters

        Returns:
            JSON string with operation result
        """
        try:
            # Validate repository context
            repo_context = self._validate_repository_context(repository_context)
            repository = repo_context.repository_full_name

            # Validate repository access
            self._validate_repository_access(repository, repo_context)

            # Create issue using the client
            result = await self.client.create_issue(
                repository=repository,
                title=title,
                description=description,
                labels=labels,
                assignees=assignees,
                **kwargs,
            )

            return json.dumps(
                {
                    "success": True,
                    "message": f"Issue created successfully in {repository}",
                    "data": result,
                },
                ensure_ascii=False,
                indent=2,
            )

        except Exception as e:
            logger.error(f"Error creating issue: {str(e)}")
            return json.dumps(
                {"success": False, "error": str(e), "error_type": type(e).__name__},
                ensure_ascii=False,
                indent=2,
            )

    async def create_pull_request(
        self,
        title: str,
        description: str,
        head_branch: str,
        base_branch: str = "main",
        repository_context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> str:
        """
        Create a pull request in the repository with context validation.

        Args:
            title: PR title
            description: PR description
            head_branch: Source branch
            base_branch: Target branch
            repository_context: Current repository context
            **kwargs: Additional platform-specific parameters

        Returns:
            JSON string with operation result
        """
        try:
            # Validate repository context
            repo_context = self._validate_repository_context(repository_context)
            repository = repo_context.repository_full_name

            # Validate repository access
            self._validate_repository_access(repository, repo_context)

            # Create pull request using the client
            result = await self.client.create_pull_request(
                repository=repository,
                title=title,
                description=description,
                head_branch=head_branch,
                base_branch=base_branch,
                **kwargs,
            )

            return json.dumps(
                {
                    "success": True,
                    "message": f"Pull request created successfully in {repository}",
                    "data": result,
                },
                ensure_ascii=False,
                indent=2,
            )

        except Exception as e:
            logger.error(f"Error creating pull request: {str(e)}")
            return json.dumps(
                {"success": False, "error": str(e), "error_type": type(e).__name__},
                ensure_ascii=False,
                indent=2,
            )

    async def check_repository_permissions(
        self, repository_context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> str:
        """
        Check repository permissions with context validation.

        Args:
            repository_context: Current repository context
            **kwargs: Additional platform-specific parameters

        Returns:
            JSON string with permission information
        """
        try:
            # Validate repository context
            repo_context = self._validate_repository_context(repository_context)
            repository = repo_context.repository_full_name

            # Validate repository access
            self._validate_repository_access(repository, repo_context)

            # Check permissions using the client
            result = await self.client.check_repository_permissions(
                repository=repository, **kwargs
            )

            return json.dumps(
                {
                    "success": True,
                    "message": f"Repository permissions retrieved for {repository}",
                    "repository": repository,
                    "permissions": result,
                    "context_validated": True,
                },
                ensure_ascii=False,
                indent=2,
            )

        except Exception as e:
            logger.error(f"Error checking repository permissions: {str(e)}")
            return json.dumps(
                {"success": False, "error": str(e), "error_type": type(e).__name__},
                ensure_ascii=False,
                indent=2,
            )

    def _validate_repository_context(
        self, repository_context: Optional[Dict[str, Any]]
    ) -> RepositoryContext:
        """Validate and convert repository context."""
        if not repository_context:
            raise ValueError("Repository context is required for secure operations")

        try:
            return RepositoryContext(**repository_context)
        except Exception as e:
            raise ValueError(f"Invalid repository context: {str(e)}")

    def _validate_repository_access(
        self, requested_repository: str, repository_context: RepositoryContext
    ) -> None:
        """Validate that the requested repository matches the current context."""
        current_repository = repository_context.repository_full_name

        if requested_repository != current_repository:
            raise PermissionError(
                f"Access denied: Requested repository '{requested_repository}' "
                f"does not match current context '{current_repository}'"
            )

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Return the name of the Git service."""
        pass
