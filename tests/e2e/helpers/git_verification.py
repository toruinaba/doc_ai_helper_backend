"""
Git service verification client for E2E tests.

This module provides functionality to verify Git operations and manage test data
across different Git services (GitHub, Forgejo) during E2E testing.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import httpx

from tests.e2e.helpers.config import E2EConfig

logger = logging.getLogger(__name__)


class GitVerificationClient:
    """
    Client for verifying Git operations and managing test data in E2E tests.
    """

    def __init__(self, config: E2EConfig):
        """Initialize the Git verification client."""
        self.config = config
        self._clients = {}

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close all HTTP clients."""
        for client in self._clients.values():
            if hasattr(client, 'aclose'):
                await client.aclose()

    def _get_client(self, service: str) -> httpx.AsyncClient:
        """Get or create HTTP client for a service."""
        if service not in self._clients:
            if service == "github":
                headers = {
                    "Authorization": f"token {self.config.github_token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "E2E-Test-Client"
                }
                self._clients[service] = httpx.AsyncClient(
                    base_url="https://api.github.com",
                    headers=headers,
                    timeout=30.0
                )
            elif service == "forgejo":
                headers = {
                    "Authorization": f"token {self.config.forgejo_token}",
                    "Accept": "application/json"
                }
                if not self.config.forgejo_token and self.config.forgejo_username and self.config.forgejo_password:
                    # Use basic auth if token not available
                    auth = (self.config.forgejo_username, self.config.forgejo_password)
                    self._clients[service] = httpx.AsyncClient(
                        base_url=f"{self.config.forgejo_base_url}/api/v1",
                        auth=auth,
                        headers={"Accept": "application/json"},
                        timeout=30.0
                    )
                else:
                    self._clients[service] = httpx.AsyncClient(
                        base_url=f"{self.config.forgejo_base_url}/api/v1",
                        headers=headers,
                        timeout=30.0
                    )
        
        return self._clients[service]

    async def verify_issue_exists(
        self,
        service: str,
        owner: str,
        repo: str,
        title_pattern: str,
        max_age_seconds: int = 300
    ) -> Optional[Dict[str, Any]]:
        """
        Verify that an issue with the given title pattern exists.

        Args:
            service: Git service name (github, forgejo)
            owner: Repository owner
            repo: Repository name
            title_pattern: Pattern to search for in issue titles
            max_age_seconds: Maximum age of issue to consider (default 5 minutes)

        Returns:
            Issue data if found, None otherwise
        """
        try:
            client = self._get_client(service)
            
            # Get recent issues
            if service == "github":
                url = f"/repos/{owner}/{repo}/issues"
            elif service == "forgejo":
                url = f"/repos/{owner}/{repo}/issues"
            else:
                raise ValueError(f"Unsupported service: {service}")

            response = await client.get(url, params={"state": "open", "per_page": 20})
            response.raise_for_status()
            
            issues = response.json()
            cutoff_time = datetime.now() - timedelta(seconds=max_age_seconds)
            
            for issue in issues:
                # Check if title contains the pattern
                if title_pattern.lower() in issue.get("title", "").lower():
                    # Parse creation time
                    created_at_str = issue.get("created_at", "")
                    try:
                        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        if created_at.replace(tzinfo=None) >= cutoff_time:
                            logger.info(f"Found matching issue: #{issue.get('number')} - {issue.get('title')}")
                            return {
                                "number": issue.get("number"),
                                "title": issue.get("title"),
                                "body": issue.get("body", ""),
                                "state": issue.get("state"),
                                "created_at": created_at_str,
                                "url": issue.get("html_url")
                            }
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to parse issue creation time: {e}")
                        continue
            
            logger.info(f"No matching issues found with pattern '{title_pattern}' in last {max_age_seconds} seconds")
            return None

        except Exception as e:
            logger.error(f"Error verifying issue existence: {e}")
            return None

    async def get_recent_issues(
        self,
        service: str,
        owner: str,
        repo: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent issues from a repository.

        Args:
            service: Git service name
            owner: Repository owner
            repo: Repository name
            limit: Maximum number of issues to return

        Returns:
            List of issue data
        """
        try:
            client = self._get_client(service)
            
            if service == "github":
                url = f"/repos/{owner}/{repo}/issues"
            elif service == "forgejo":
                url = f"/repos/{owner}/{repo}/issues"
            else:
                raise ValueError(f"Unsupported service: {service}")

            response = await client.get(url, params={
                "state": "all",
                "per_page": limit,
                "sort": "created",
                "direction": "desc"
            })
            response.raise_for_status()
            
            return response.json()

        except Exception as e:
            logger.error(f"Error getting recent issues: {e}")
            return []

    async def cleanup_test_issues(
        self,
        service: str,
        owner: str,
        repo: str,
        title_pattern: str,
        max_age_hours: int = 24
    ) -> int:
        """
        Clean up test issues created during E2E tests.

        Args:
            service: Git service name
            owner: Repository owner
            repo: Repository name
            title_pattern: Pattern to search for in issue titles
            max_age_hours: Maximum age of issues to clean up

        Returns:
            Number of issues cleaned up
        """
        try:
            client = self._get_client(service)
            
            # Get all open issues
            if service == "github":
                url = f"/repos/{owner}/{repo}/issues"
            elif service == "forgejo":
                url = f"/repos/{owner}/{repo}/issues"
            else:
                raise ValueError(f"Unsupported service: {service}")

            response = await client.get(url, params={"state": "open", "per_page": 100})
            response.raise_for_status()
            
            issues = response.json()
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            cleaned_count = 0
            
            for issue in issues:
                title = issue.get("title", "")
                if title_pattern.lower() in title.lower():
                    # Check if it's a test issue created recently
                    created_at_str = issue.get("created_at", "")
                    try:
                        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        if created_at.replace(tzinfo=None) >= cutoff_time:
                            # This is a recent test issue - close it
                            issue_number = issue.get("number")
                            
                            if service == "github":
                                close_url = f"/repos/{owner}/{repo}/issues/{issue_number}"
                            elif service == "forgejo":
                                close_url = f"/repos/{owner}/{repo}/issues/{issue_number}"
                            
                            close_response = await client.patch(close_url, json={"state": "closed"})
                            if close_response.status_code == 200:
                                logger.info(f"Closed test issue #{issue_number}: {title}")
                                cleaned_count += 1
                            else:
                                logger.warning(f"Failed to close issue #{issue_number}: {close_response.status_code}")
                    
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to parse issue creation time for cleanup: {e}")
                        continue
            
            logger.info(f"Cleaned up {cleaned_count} test issues")
            return cleaned_count

        except Exception as e:
            logger.error(f"Error during test issue cleanup: {e}")
            return 0

    async def verify_repository_access(self, service: str, owner: str, repo: str) -> bool:
        """
        Verify that we have access to a repository.

        Args:
            service: Git service name
            owner: Repository owner
            repo: Repository name

        Returns:
            True if repository is accessible, False otherwise
        """
        try:
            client = self._get_client(service)
            
            if service == "github":
                url = f"/repos/{owner}/{repo}"
            elif service == "forgejo":
                url = f"/repos/{owner}/{repo}"
            else:
                raise ValueError(f"Unsupported service: {service}")

            response = await client.get(url)
            success = response.status_code == 200
            
            if success:
                logger.info(f"Successfully verified access to {service}:{owner}/{repo}")
            else:
                logger.warning(f"Cannot access {service}:{owner}/{repo} - status: {response.status_code}")
            
            return success

        except Exception as e:
            logger.error(f"Error verifying repository access: {e}")
            return False

    async def create_test_issue(
        self,
        service: str,
        owner: str,
        repo: str,
        title: str,
        body: str
    ) -> Optional[Dict[str, Any]]:
        """
        Create a test issue for verification purposes.

        Args:
            service: Git service name
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue body

        Returns:
            Created issue data if successful, None otherwise
        """
        try:
            client = self._get_client(service)
            
            if service == "github":
                url = f"/repos/{owner}/{repo}/issues"
            elif service == "forgejo":
                url = f"/repos/{owner}/{repo}/issues"
            else:
                raise ValueError(f"Unsupported service: {service}")

            issue_data = {
                "title": title,
                "body": body
            }

            response = await client.post(url, json=issue_data)
            response.raise_for_status()
            
            created_issue = response.json()
            logger.info(f"Created test issue #{created_issue.get('number')}: {title}")
            
            return {
                "number": created_issue.get("number"),
                "title": created_issue.get("title"),
                "body": created_issue.get("body", ""),
                "state": created_issue.get("state"),
                "created_at": created_issue.get("created_at"),
                "url": created_issue.get("html_url")
            }

        except Exception as e:
            logger.error(f"Error creating test issue: {e}")
            return None