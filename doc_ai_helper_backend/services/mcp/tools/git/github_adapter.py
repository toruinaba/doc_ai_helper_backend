"""
GitHub adapter for MCP Git tools.

This module provides GitHub-specific implementation of the MCP Git tools
abstraction, wrapping the existing GitHub client and tools.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from .base import MCPGitClientBase, MCPGitToolsBase
from ....github.github_client import GitHubClient
from ....github.exceptions import (
    GitHubException,
    GitHubRepositoryNotFoundError,
    GitHubPermissionError,
)

logger = logging.getLogger(__name__)


class MCPGitHubClient(MCPGitClientBase):
    """GitHub API client for MCP tools."""

    def __init__(self, access_token: Optional[str] = None, **kwargs):
        """Initialize GitHub client."""
        super().__init__(**kwargs)
        self.github_client = GitHubClient(token=access_token)

    async def create_issue(
        self,
        repository: str,
        title: str,
        description: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a GitHub issue."""
        try:
            result = await self.github_client.create_issue(
                repository=repository,
                title=title,
                body=description,
                labels=labels or [],
                assignees=assignees or [],
            )

            return {
                "issue_number": result.get("number"),
                "issue_url": result.get("html_url"),
                "title": result.get("title"),
                "state": result.get("state"),
                "created_at": result.get("created_at"),
            }

        except GitHubException as e:
            raise e
        except Exception as e:
            raise GitHubException(f"Failed to create GitHub issue: {str(e)}")

    async def create_pull_request(
        self,
        repository: str,
        title: str,
        description: str,
        head_branch: str,
        base_branch: str = "main",
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a GitHub pull request."""
        try:
            result = await self.github_client.create_pull_request(
                repository=repository,
                title=title,
                body=description,
                head=head_branch,
                base=base_branch,
            )

            return {
                "pr_number": result.get("number"),
                "pr_url": result.get("html_url"),
                "title": result.get("title"),
                "state": result.get("state"),
                "head_branch": result.get("head", {}).get("ref"),
                "base_branch": result.get("base", {}).get("ref"),
                "created_at": result.get("created_at"),
            }

        except GitHubException as e:
            raise e
        except Exception as e:
            raise GitHubException(f"Failed to create GitHub pull request: {str(e)}")

    async def check_repository_permissions(
        self, repository: str, **kwargs
    ) -> Dict[str, Any]:
        """Check GitHub repository permissions."""
        try:
            permissions = await self.github_client.check_repository_permissions(
                repository
            )

            return {
                "repository": repository,
                "permissions": permissions,
                "can_read": permissions.get("pull", False),
                "can_write": permissions.get("push", False),
                "can_admin": permissions.get("admin", False),
            }

        except GitHubException as e:
            raise e
        except Exception as e:
            raise GitHubException(
                f"Failed to check GitHub repository permissions: {str(e)}"
            )


class MCPGitHubAdapter(MCPGitToolsBase):
    """GitHub-specific MCP Git tools adapter."""

    def __init__(self, access_token: Optional[str] = None, **kwargs):
        """Initialize GitHub adapter."""
        client = MCPGitHubClient(access_token=access_token, **kwargs)
        super().__init__(client)
        self.access_token = access_token

    @property
    def service_name(self) -> str:
        """Return the service name."""
        return "github"

    async def create_issue(
        self,
        title: str,
        description: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        repository_context: Optional[Dict[str, Any]] = None,
        github_token: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Create a GitHub issue with enhanced error handling.

        Args:
            title: Issue title
            description: Issue description
            labels: Issue labels
            assignees: Issue assignees
            repository_context: Current repository context
            github_token: GitHub access token (overrides instance token)
            **kwargs: Additional GitHub-specific parameters

        Returns:
            JSON string with operation result
        """
        # Update client token if provided
        if github_token and github_token != self.access_token:
            self.client = MCPGitHubClient(access_token=github_token)
            self.access_token = github_token

        try:
            return await super().create_issue(
                title=title,
                description=description,
                labels=labels,
                assignees=assignees,
                repository_context=repository_context,
                **kwargs,
            )
        except GitHubRepositoryNotFoundError:
            return json.dumps(
                {
                    "success": False,
                    "error": "指定されたリポジトリが見つかりません。リポジトリ名とアクセス権限を確認してください。",
                    "error_type": "repository_not_found",
                },
                ensure_ascii=False,
                indent=2,
            )
        except GitHubPermissionError:
            return json.dumps(
                {
                    "success": False,
                    "error": "リポジトリへのアクセス権限がありません。GitHubトークンの権限を確認してください。",
                    "error_type": "permission_denied",
                },
                ensure_ascii=False,
                indent=2,
            )
        except Exception as e:
            logger.error(f"Unexpected error in GitHub issue creation: {str(e)}")
            return json.dumps(
                {
                    "success": False,
                    "error": f"予期しないエラーが発生しました: {str(e)}",
                    "error_type": "unexpected_error",
                },
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
        github_token: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Create a GitHub pull request with enhanced error handling.

        Args:
            title: PR title
            description: PR description
            head_branch: Source branch
            base_branch: Target branch
            repository_context: Current repository context
            github_token: GitHub access token (overrides instance token)
            **kwargs: Additional GitHub-specific parameters

        Returns:
            JSON string with operation result
        """
        # Update client token if provided
        if github_token and github_token != self.access_token:
            self.client = MCPGitHubClient(access_token=github_token)
            self.access_token = github_token

        try:
            return await super().create_pull_request(
                title=title,
                description=description,
                head_branch=head_branch,
                base_branch=base_branch,
                repository_context=repository_context,
                **kwargs,
            )
        except GitHubRepositoryNotFoundError:
            return json.dumps(
                {
                    "success": False,
                    "error": "指定されたリポジトリが見つかりません。リポジトリ名とアクセス権限を確認してください。",
                    "error_type": "repository_not_found",
                },
                ensure_ascii=False,
                indent=2,
            )
        except GitHubPermissionError:
            return json.dumps(
                {
                    "success": False,
                    "error": "リポジトリへのアクセス権限がありません。GitHubトークンの権限を確認してください。",
                    "error_type": "permission_denied",
                },
                ensure_ascii=False,
                indent=2,
            )
        except Exception as e:
            logger.error(f"Unexpected error in GitHub pull request creation: {str(e)}")
            return json.dumps(
                {
                    "success": False,
                    "error": f"予期しないエラーが発生しました: {str(e)}",
                    "error_type": "unexpected_error",
                },
                ensure_ascii=False,
                indent=2,
            )

    async def check_repository_permissions(
        self,
        repository_context: Optional[Dict[str, Any]] = None,
        github_token: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Check GitHub repository permissions with enhanced error handling.

        Args:
            repository_context: Current repository context
            github_token: GitHub access token (overrides instance token)
            **kwargs: Additional GitHub-specific parameters

        Returns:
            JSON string with permission information
        """
        # Update client token if provided
        if github_token and github_token != self.access_token:
            self.client = MCPGitHubClient(access_token=github_token)
            self.access_token = github_token

        try:
            return await super().check_repository_permissions(
                repository_context=repository_context, **kwargs
            )
        except GitHubRepositoryNotFoundError:
            return json.dumps(
                {
                    "success": False,
                    "error": "指定されたリポジトリが見つかりません。リポジトリ名とアクセス権限を確認してください。",
                    "error_type": "repository_not_found",
                },
                ensure_ascii=False,
                indent=2,
            )
        except GitHubPermissionError:
            return json.dumps(
                {
                    "success": False,
                    "error": "リポジトリへのアクセス権限がありません。GitHubトークンの権限を確認してください。",
                    "error_type": "permission_denied",
                },
                ensure_ascii=False,
                indent=2,
            )
        except Exception as e:
            logger.error(f"Unexpected error in GitHub permission check: {str(e)}")
            return json.dumps(
                {
                    "success": False,
                    "error": f"予期しないエラーが発生しました: {str(e)}",
                    "error_type": "unexpected_error",
                },
                ensure_ascii=False,
                indent=2,
            )
