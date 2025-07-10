"""
Forgejo verification client for E2E tests.

This module provides a client for directly verifying results in Forgejo
during end-to-end tests.
"""

import asyncio
from typing import Dict, Any, Optional, List
import httpx
import logging

logger = logging.getLogger(__name__)


class ForgejoVerificationClient:
    """
    Client for verifying results directly in Forgejo during E2E tests.

    This client is used to verify that MCP tools have actually created
    issues, pull requests, etc. in the Forgejo instance.
    """

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        verify_ssl: bool = True,
        timeout: int = 30,
    ):
        """
        Initialize the Forgejo verification client.

        Args:
            base_url: Base URL of the Forgejo instance
            token: Access token (preferred authentication method)
            username: Username for basic auth (alternative to token)
            password: Password for basic auth (alternative to token)
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Set up authentication headers
        headers = {"Content-Type": "application/json"}
        auth = None

        if token:
            headers["Authorization"] = f"token {token}"
        elif username and password:
            auth = (username, password)

        self._client = httpx.AsyncClient(
            headers=headers, auth=auth, verify=verify_ssl, timeout=timeout
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._client.aclose()

    async def check_connection(self) -> bool:
        """
        Check if the Forgejo instance is accessible.

        Returns:
            True if accessible, False otherwise
        """
        try:
            response = await self._client.get(f"{self.base_url}/api/v1/version")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Forgejo connection check failed: {e}")
            return False

    async def get_issue(
        self, owner: str, repo: str, issue_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific issue from Forgejo.

        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            Issue data as dictionary, or None if not found
        """
        try:
            url = f"{self.base_url}/api/v1/repos/{owner}/{repo}/issues/{issue_number}"
            response = await self._client.get(url)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to get issue {issue_number}: {e}")
            return None

    async def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        List issues in a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state (open, closed, all)
            labels: Comma-separated list of label names
            limit: Maximum number of issues to return

        Returns:
            List of issue data dictionaries
        """
        try:
            url = f"{self.base_url}/api/v1/repos/{owner}/{repo}/issues"
            params = {"state": state, "limit": limit}
            if labels:
                params["labels"] = labels

            response = await self._client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to list issues: {e}")
            return []

    async def verify_issue_exists(
        self,
        owner: str,
        repo: str,
        title_pattern: Optional[str] = None,
        content_pattern: Optional[str] = None,
        labels: Optional[List[str]] = None,
        max_age_seconds: Optional[int] = 300,  # 5 minutes
    ) -> Optional[Dict[str, Any]]:
        """
        Verify that an issue exists matching the given criteria.

        Args:
            owner: Repository owner
            repo: Repository name
            title_pattern: Pattern to search for in the title
            content_pattern: Pattern to search for in the body
            labels: List of required labels
            max_age_seconds: Maximum age of the issue in seconds

        Returns:
            Issue data if found, None otherwise
        """
        issues = await self.list_issues(owner, repo, state="all")

        for issue in issues:
            # Check title pattern
            if title_pattern and title_pattern not in issue.get("title", ""):
                continue

            # Check content pattern
            if content_pattern and content_pattern not in issue.get("body", ""):
                continue

            # Check labels
            if labels:
                issue_labels = [
                    label.get("name", "") for label in issue.get("labels", [])
                ]
                if not all(label in issue_labels for label in labels):
                    continue

            # Check age if specified
            if max_age_seconds:
                from datetime import datetime, timezone
                import dateutil.parser

                created_at = dateutil.parser.parse(issue.get("created_at", ""))
                age = (datetime.now(timezone.utc) - created_at).total_seconds()
                if age > max_age_seconds:
                    continue

            logger.info(f"Found matching issue: #{issue['number']} - {issue['title']}")
            return issue

        logger.warning(
            f"No matching issue found with criteria: title={title_pattern}, content={content_pattern}"
        )
        return None

    async def close_issue(self, owner: str, repo: str, issue_number: int) -> bool:
        """
        Close an issue (for cleanup purposes).

        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/api/v1/repos/{owner}/{repo}/issues/{issue_number}"
            payload = {"state": "closed"}

            response = await self._client.patch(url, json=payload)
            response.raise_for_status()

            logger.info(f"Closed issue #{issue_number}")
            return True
        except Exception as e:
            logger.error(f"Failed to close issue #{issue_number}: {e}")
            return False

    async def cleanup_test_issues(
        self,
        owner: str,
        repo: str,
        test_marker: str = "[E2E-TEST]",
        max_age_seconds: int = 3600,  # 1 hour
    ) -> int:
        """
        Clean up test issues by closing them.

        Args:
            owner: Repository owner
            repo: Repository name
            test_marker: Marker string to identify test issues
            max_age_seconds: Maximum age of issues to clean up

        Returns:
            Number of issues cleaned up
        """
        issues = await self.list_issues(owner, repo, state="open")
        cleaned_count = 0

        for issue in issues:
            title = issue.get("title", "")
            body = issue.get("body", "")

            # Check if this is a test issue
            if test_marker not in title and test_marker not in body:
                continue

            # Check age
            from datetime import datetime, timezone
            import dateutil.parser

            created_at = dateutil.parser.parse(issue.get("created_at", ""))
            age = (datetime.now(timezone.utc) - created_at).total_seconds()

            if age <= max_age_seconds:
                issue_number = issue.get("number")
                if await self.close_issue(owner, repo, issue_number):
                    cleaned_count += 1

        logger.info(f"Cleaned up {cleaned_count} test issues")
        return cleaned_count

    async def get_repository_info(
        self, owner: str, repo: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get repository information.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository information or None if not found
        """
        try:
            url = f"{self.base_url}/api/v1/repos/{owner}/{repo}"
            response = await self._client.get(url)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to get repository info: {e}")
            return None
