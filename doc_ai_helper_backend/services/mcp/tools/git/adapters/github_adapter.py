"""
GitHub adapter for Git operations.

This module implements the GitHub-specific adapter for Git operations,
using the GitHub REST API v4 for all interactions.
"""

import asyncio
from typing import Dict, Any, List, Optional
import logging
import aiohttp
import json
from urllib.parse import urljoin

from .base_adapter import BaseGitAdapter, GitOperationResult
from ..context import RepositoryContext, CredentialManager

logger = logging.getLogger(__name__)


class GitHubAdapter(BaseGitAdapter):
    """
    GitHub-specific implementation of Git operations.

    This adapter uses the GitHub REST API to perform Git operations
    such as creating issues, pull requests, and managing repository content.
    """

    def __init__(self, repository_context: RepositoryContext):
        """Initialize GitHub adapter."""
        self.base_api_url = "https://api.github.com"
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers: Dict[str, str] = {}

        super().__init__(repository_context)

    def _initialize_client(self) -> None:
        """Initialize GitHub API client with authentication."""
        # Get credentials for GitHub
        credential_manager = CredentialManager()
        credentials = credential_manager.get_credentials(self.repository_context)

        if not credentials or not credentials.get("token"):
            raise ValueError(
                f"No GitHub token found for repository {self.repository_context.full_name}"
            )

        # Set up headers for GitHub API
        self.headers = {
            "Authorization": f"token {credentials['token']}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "doc-ai-helper-backend/1.0",
            "Content-Type": "application/json",
        }

        self.logger.debug(
            f"Initialized GitHub adapter for {self.repository_context.full_name}"
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the GitHub API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            aiohttp.ClientError: If request fails
        """
        url = urljoin(self.base_api_url, endpoint)
        session = await self._get_session()

        try:
            async with session.request(
                method=method, url=url, json=data, params=params
            ) as response:
                response_data = await response.json()

                if response.status >= 400:
                    error_msg = response_data.get("message", f"HTTP {response.status}")
                    self.logger.error(f"GitHub API error: {error_msg}")
                    raise aiohttp.ClientError(f"GitHub API error: {error_msg}")

                return response_data

        except aiohttp.ClientError:
            raise
        except Exception as e:
            self.logger.error(f"Request to {url} failed: {str(e)}")
            raise aiohttp.ClientError(f"Request failed: {str(e)}")

    async def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        milestone: Optional[str] = None,
    ) -> GitOperationResult:
        """Create an issue in the GitHub repository."""
        try:
            endpoint = f"/repos/{self.repository_context.owner}/{self.repository_context.repo}/issues"

            issue_data = {
                "title": title,
                "body": body,
            }

            if labels:
                issue_data["labels"] = labels
            if assignees:
                issue_data["assignees"] = assignees
            if milestone:
                # Note: GitHub expects milestone number, not name
                # This is a simplified implementation
                issue_data["milestone"] = milestone

            response_data = await self._make_request("POST", endpoint, data=issue_data)

            return GitOperationResult(
                success=True,
                data=response_data,
                url=response_data.get("html_url"),
                operation="create_issue",
            )

        except Exception as e:
            self.logger.error(f"Failed to create issue: {str(e)}")
            return GitOperationResult(
                success=False, error=str(e), operation="create_issue"
            )

    async def create_pull_request(
        self,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
        draft: bool = False,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        reviewers: Optional[List[str]] = None,
    ) -> GitOperationResult:
        """Create a pull request in the GitHub repository."""
        try:
            endpoint = f"/repos/{self.repository_context.owner}/{self.repository_context.repo}/pulls"

            pr_data = {
                "title": title,
                "body": body,
                "head": head_branch,
                "base": base_branch,
                "draft": draft,
            }

            response_data = await self._make_request("POST", endpoint, data=pr_data)

            # Apply labels and assignees if specified
            if labels or assignees:
                issue_endpoint = f"/repos/{self.repository_context.owner}/{self.repository_context.repo}/issues/{response_data['number']}"
                update_data = {}
                if labels:
                    update_data["labels"] = labels
                if assignees:
                    update_data["assignees"] = assignees

                await self._make_request("PATCH", issue_endpoint, data=update_data)

            # Request reviewers if specified
            if reviewers:
                review_endpoint = f"/repos/{self.repository_context.owner}/{self.repository_context.repo}/pulls/{response_data['number']}/requested_reviewers"
                review_data = {"reviewers": reviewers}
                await self._make_request("POST", review_endpoint, data=review_data)

            return GitOperationResult(
                success=True,
                data=response_data,
                url=response_data.get("html_url"),
                operation="create_pull_request",
            )

        except Exception as e:
            self.logger.error(f"Failed to create pull request: {str(e)}")
            return GitOperationResult(
                success=False, error=str(e), operation="create_pull_request"
            )

    async def get_repository_info(self) -> GitOperationResult:
        """Get GitHub repository information."""
        try:
            endpoint = (
                f"/repos/{self.repository_context.owner}/{self.repository_context.repo}"
            )
            response_data = await self._make_request("GET", endpoint)

            return GitOperationResult(
                success=True,
                data=response_data,
                url=response_data.get("html_url"),
                operation="get_repository_info",
            )

        except Exception as e:
            self.logger.error(f"Failed to get repository info: {str(e)}")
            return GitOperationResult(
                success=False, error=str(e), operation="get_repository_info"
            )

    async def list_branches(self) -> GitOperationResult:
        """List GitHub repository branches."""
        try:
            endpoint = f"/repos/{self.repository_context.owner}/{self.repository_context.repo}/branches"
            response_data = await self._make_request("GET", endpoint)

            # Extract branch names
            branches = [branch["name"] for branch in response_data]

            return GitOperationResult(
                success=True, data={"branches": branches}, operation="list_branches"
            )

        except Exception as e:
            self.logger.error(f"Failed to list branches: {str(e)}")
            return GitOperationResult(
                success=False, error=str(e), operation="list_branches"
            )

    async def get_file_content(
        self, file_path: str, branch: str = "main"
    ) -> GitOperationResult:
        """Get content of a file from the GitHub repository."""
        try:
            endpoint = f"/repos/{self.repository_context.owner}/{self.repository_context.repo}/contents/{file_path}"
            params = {"ref": branch}

            response_data = await self._make_request("GET", endpoint, params=params)

            # Decode base64 content if it's a file
            if response_data.get("type") == "file" and "content" in response_data:
                import base64

                content = base64.b64decode(response_data["content"]).decode("utf-8")
                response_data["decoded_content"] = content

            return GitOperationResult(
                success=True, data=response_data, operation="get_file_content"
            )

        except Exception as e:
            self.logger.error(f"Failed to get file content: {str(e)}")
            return GitOperationResult(
                success=False, error=str(e), operation="get_file_content"
            )

    async def create_or_update_file(
        self,
        file_path: str,
        content: str,
        commit_message: str,
        branch: str = "main",
        create_branch_if_not_exists: bool = False,
    ) -> GitOperationResult:
        """Create or update a file in the GitHub repository."""
        try:
            # First, try to get the existing file to obtain the SHA
            existing_file_result = await self.get_file_content(file_path, branch)

            endpoint = f"/repos/{self.repository_context.owner}/{self.repository_context.repo}/contents/{file_path}"

            import base64

            file_data = {
                "message": commit_message,
                "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
                "branch": branch,
            }

            # If file exists, include SHA for update
            if existing_file_result.success and "sha" in existing_file_result.data:
                file_data["sha"] = existing_file_result.data["sha"]

            response_data = await self._make_request("PUT", endpoint, data=file_data)

            return GitOperationResult(
                success=True,
                data=response_data,
                url=response_data.get("content", {}).get("html_url"),
                operation="create_or_update_file",
            )

        except Exception as e:
            self.logger.error(f"Failed to create/update file: {str(e)}")
            return GitOperationResult(
                success=False, error=str(e), operation="create_or_update_file"
            )

    async def close(self) -> None:
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.logger.debug("Closed GitHub adapter session")

    def __del__(self):
        """Cleanup when adapter is destroyed."""
        if hasattr(self, "session") and self.session and not self.session.closed:
            # Try to close session, but don't block if event loop is gone
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
            except RuntimeError:
                pass  # Event loop is gone, nothing we can do
