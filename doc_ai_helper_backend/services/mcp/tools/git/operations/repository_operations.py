"""
Repository operations for Git repositories.

This module provides high-level operations for managing repository data
and metadata across different Git hosting services.
"""

from typing import Dict, Any, List, Optional, Union
import logging

from ..adapters import BaseGitAdapter, GitOperationResult
from ..context import RepositoryContext
from ..service_resolver import resolve_git_adapter

logger = logging.getLogger(__name__)


class RepositoryOperations:
    """
    High-level operations for managing repository data across Git services.

    This class provides a service-agnostic interface for repository operations,
    automatically resolving the appropriate adapter based on repository context.
    """

    def __init__(self, repository_context: RepositoryContext):
        """
        Initialize repository operations.

        Args:
            repository_context: Repository context for determining service
        """
        self.repository_context = repository_context
        self.adapter: Optional[BaseGitAdapter] = None
        self.logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

    async def _get_adapter(self) -> BaseGitAdapter:
        """Get or create the appropriate Git service adapter."""
        if self.adapter is None:
            self.adapter = resolve_git_adapter(self.repository_context)
        return self.adapter

    async def get_repository_info(self) -> GitOperationResult:
        """
        Get comprehensive repository information.

        Returns:
            GitOperationResult containing repository metadata
        """
        try:
            adapter = await self._get_adapter()

            self.logger.debug(
                f"Getting repository info for {self.repository_context.full_name}"
            )

            result = await adapter.get_repository_info()

            if result.success:
                self.logger.debug(
                    f"Successfully retrieved repository info for {self.repository_context.full_name}"
                )
            else:
                self.logger.error(
                    f"Failed to get repository info for {self.repository_context.full_name}: {result.error}"
                )

            return result

        except Exception as e:
            self.logger.error(f"Error getting repository info: {str(e)}")
            return GitOperationResult(
                success=False,
                error=f"Failed to get repository info: {str(e)}",
                operation="get_repository_info",
            )

    async def list_branches(self) -> GitOperationResult:
        """
        List all branches in the repository.

        Returns:
            GitOperationResult containing list of branch names
        """
        try:
            adapter = await self._get_adapter()

            self.logger.debug(
                f"Listing branches for {self.repository_context.full_name}"
            )

            result = await adapter.list_branches()

            if result.success:
                branch_count = len(result.data.get("branches", []))
                self.logger.debug(
                    f"Successfully listed {branch_count} branches for {self.repository_context.full_name}"
                )
            else:
                self.logger.error(
                    f"Failed to list branches for {self.repository_context.full_name}: {result.error}"
                )

            return result

        except Exception as e:
            self.logger.error(f"Error listing branches: {str(e)}")
            return GitOperationResult(
                success=False,
                error=f"Failed to list branches: {str(e)}",
                operation="list_branches",
            )

    async def get_file_content(
        self, file_path: str, branch: str = "main"
    ) -> GitOperationResult:
        """
        Get content of a file from the repository.

        Args:
            file_path: Path to the file in the repository
            branch: Branch name to read from

        Returns:
            GitOperationResult containing file content
        """
        try:
            adapter = await self._get_adapter()

            self.logger.debug(
                f"Getting file content for {file_path} from {branch} "
                f"in {self.repository_context.full_name}"
            )

            result = await adapter.get_file_content(file_path, branch)

            if result.success:
                self.logger.debug(
                    f"Successfully retrieved file {file_path} from {self.repository_context.full_name}"
                )
            else:
                self.logger.error(
                    f"Failed to get file {file_path} from {self.repository_context.full_name}: {result.error}"
                )

            return result

        except Exception as e:
            self.logger.error(f"Error getting file content: {str(e)}")
            return GitOperationResult(
                success=False,
                error=f"Failed to get file content: {str(e)}",
                operation="get_file_content",
            )

    async def create_or_update_file(
        self,
        file_path: str,
        content: str,
        commit_message: str,
        branch: str = "main",
        create_branch_if_not_exists: bool = False,
    ) -> GitOperationResult:
        """
        Create or update a file in the repository.

        Args:
            file_path: Path to the file in the repository
            content: New file content
            commit_message: Commit message
            branch: Branch to commit to
            create_branch_if_not_exists: Whether to create branch if it doesn't exist

        Returns:
            GitOperationResult with operation outcome
        """
        try:
            adapter = await self._get_adapter()

            self.logger.info(
                f"Creating/updating file {file_path} in {branch} "
                f"for {self.repository_context.full_name}"
            )

            result = await adapter.create_or_update_file(
                file_path=file_path,
                content=content,
                commit_message=commit_message,
                branch=branch,
                create_branch_if_not_exists=create_branch_if_not_exists,
            )

            if result.success:
                self.logger.info(
                    f"Successfully created/updated file {file_path} in {self.repository_context.full_name}"
                )
            else:
                self.logger.error(
                    f"Failed to create/update file {file_path} in {self.repository_context.full_name}: {result.error}"
                )

            return result

        except Exception as e:
            self.logger.error(f"Error creating/updating file: {str(e)}")
            return GitOperationResult(
                success=False,
                error=f"Failed to create/update file: {str(e)}",
                operation="create_or_update_file",
            )

    async def get_repository_summary(self) -> GitOperationResult:
        """
        Get a comprehensive summary of the repository.

        This method combines repository info and branch information
        to provide a complete overview.

        Returns:
            GitOperationResult containing repository summary
        """
        try:
            # Get repository info and branches in parallel
            repo_info_result = await self.get_repository_info()
            branches_result = await self.list_branches()

            summary_data = {
                "repository_info": (
                    repo_info_result.data if repo_info_result.success else None
                ),
                "branches": (
                    branches_result.data.get("branches", [])
                    if branches_result.success
                    else []
                ),
                "repository_context": {
                    "service_type": self.repository_context.service_type.value,
                    "base_url": self.repository_context.base_url,
                    "owner": self.repository_context.owner,
                    "repo": self.repository_context.repo,
                    "full_name": self.repository_context.full_name,
                },
            }

            # Determine success based on critical operations
            success = repo_info_result.success
            error_messages = []

            if not repo_info_result.success:
                error_messages.append(f"Repository info: {repo_info_result.error}")
            if not branches_result.success:
                error_messages.append(f"Branches: {branches_result.error}")

            error_message = "; ".join(error_messages) if error_messages else None

            return GitOperationResult(
                success=success,
                data=summary_data,
                error=error_message,
                operation="get_repository_summary",
            )

        except Exception as e:
            self.logger.error(f"Error getting repository summary: {str(e)}")
            return GitOperationResult(
                success=False,
                error=f"Failed to get repository summary: {str(e)}",
                operation="get_repository_summary",
            )

    async def get_recent_activity_summary(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get a summary of recent repository activity.

        Note: This is a placeholder for future implementation.
        Different Git services have different APIs for activity data.

        Args:
            limit: Maximum number of activities to retrieve

        Returns:
            Dictionary containing activity summary
        """
        # This would need to be implemented based on each service's API
        # For now, return basic repository information
        repo_summary = await self.get_repository_summary()

        return {
            "repository": self.repository_context.full_name,
            "service": self.repository_context.service_type.value,
            "summary_available": repo_summary.success,
            "note": "Recent activity tracking to be implemented based on service-specific APIs",
        }

    async def close(self) -> None:
        """Close the adapter connection."""
        if self.adapter:
            await self.adapter.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
