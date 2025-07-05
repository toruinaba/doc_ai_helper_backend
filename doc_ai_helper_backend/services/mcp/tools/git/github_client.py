"""GitHub API client for repository operations."""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import httpx

from .auth_manager import GitHubAuthManager
from doc_ai_helper_backend.core.exceptions import (
    GitHubAPIError,
    GitHubAuthError,
    GitHubRateLimitError,
    GitHubRepositoryNotFoundError,
    GitHubPermissionError,
)

logger = logging.getLogger(__name__)


class GitHubClient:
    """GitHub API client for repository operations."""

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: str = "https://api.github.com",
        timeout: float = 30.0,
    ):
        """
        Initialize GitHub client.

        Args:
            token: GitHub Personal Access Token.
            base_url: GitHub API base URL.
            timeout: Request timeout in seconds.
        """
        self.auth_manager = GitHubAuthManager(token)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Validate token format
        if not self.auth_manager.validate_token():
            logger.warning("GitHub token format appears invalid")

        logger.info(
            f"GitHub client initialized with token: {self.auth_manager.mask_token()}"
        )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make authenticated request to GitHub API.

        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint (without base URL).
            data: Request body data.
            params: Query parameters.

        Returns:
            Response data as dictionary.

        Raises:
            GitHubAPIError: For API-related errors.
            GitHubAuthError: For authentication errors.
            GitHubRateLimitError: For rate limit errors.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self.auth_manager.get_auth_headers()

        if data:
            headers["Content-Type"] = "application/json"

        logger.debug(f"Making {method} request to {url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params,
                )

                return await self._handle_response(response)

        except httpx.TimeoutException:
            raise GitHubAPIError("Request timeout", status_code=408)
        except httpx.RequestError as e:
            raise GitHubAPIError(f"Request failed: {str(e)}", status_code=500)

    async def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Handle GitHub API response.

        Args:
            response: HTTP response object.

        Returns:
            Response data as dictionary.

        Raises:
            GitHubAPIError: For various API errors.
        """
        status_code = response.status_code

        try:
            response_data = response.json() if response.content else {}
        except json.JSONDecodeError:
            response_data = {"message": response.text}

        # Success responses
        if 200 <= status_code < 300:
            return response_data

        # Error handling
        error_message = response_data.get("message", f"HTTP {status_code}")

        if status_code == 401:
            raise GitHubAuthError(f"Authentication failed: {error_message}")
        elif status_code == 403:
            if "rate limit" in error_message.lower():
                reset_time = response.headers.get("X-RateLimit-Reset")
                raise GitHubRateLimitError(int(reset_time) if reset_time else None)
            else:
                raise GitHubPermissionError(error_message)
        elif status_code == 404:
            raise GitHubRepositoryNotFoundError(error_message)
        else:
            raise GitHubAPIError(error_message, status_code, response_data)

    def _parse_repository(self, repository: str) -> Tuple[str, str]:
        """
        Parse repository string into owner and repo name.

        Args:
            repository: Repository in "owner/repo" format.

        Returns:
            Tuple of (owner, repo).

        Raises:
            ValueError: If repository format is invalid.
        """
        if "/" not in repository:
            raise ValueError(
                f"Invalid repository format: {repository}. Expected 'owner/repo'"
            )

        parts = repository.split("/")
        if len(parts) != 2 or not all(parts):
            raise ValueError(
                f"Invalid repository format: {repository}. Expected 'owner/repo'"
            )

        return parts[0], parts[1]

    async def get_repository_info(self, repository: str) -> Dict[str, Any]:
        """
        Get repository information.

        Args:
            repository: Repository in "owner/repo" format.

        Returns:
            Repository information.
        """
        owner, repo = self._parse_repository(repository)
        return await self._make_request("GET", f"/repos/{owner}/{repo}")

    async def check_repository_permissions(self, repository: str) -> Dict[str, bool]:
        """
        Check permissions for a repository.

        Args:
            repository: Repository in "owner/repo" format.

        Returns:
            Dictionary with permission flags.
        """
        try:
            repo_info = await self.get_repository_info(repository)
            permissions = repo_info.get("permissions", {})

            return {
                "read": permissions.get("pull", False),
                "write": permissions.get("push", False),
                "admin": permissions.get("admin", False),
                "issues": repo_info.get("has_issues", False),
                "pull_requests": True,  # Most repos allow PRs
            }
        except GitHubRepositoryNotFoundError:
            return {
                "read": False,
                "write": False,
                "admin": False,
                "issues": False,
                "pull_requests": False,
            }

    async def create_issue(
        self,
        repository: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create an issue in the repository.

        Args:
            repository: Repository in "owner/repo" format.
            title: Issue title.
            body: Issue body/description.
            labels: List of label names.
            assignees: List of GitHub usernames to assign.

        Returns:
            Created issue information.
        """
        owner, repo = self._parse_repository(repository)

        issue_data = {
            "title": title,
            "body": body,
        }

        if labels:
            issue_data["labels"] = labels
        if assignees:
            issue_data["assignees"] = assignees

        logger.info(f"Creating issue in {repository}: {title}")
        return await self._make_request(
            "POST", f"/repos/{owner}/{repo}/issues", data=issue_data
        )

    async def create_pull_request(
        self,
        repository: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
    ) -> Dict[str, Any]:
        """
        Create a pull request in the repository.

        Args:
            repository: Repository in "owner/repo" format.
            title: PR title.
            body: PR description.
            head_branch: Source branch name.
            base_branch: Target branch name.

        Returns:
            Created pull request information.
        """
        owner, repo = self._parse_repository(repository)

        pr_data = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch,
        }

        logger.info(f"Creating pull request in {repository}: {title}")
        return await self._make_request(
            "POST", f"/repos/{owner}/{repo}/pulls", data=pr_data
        )
