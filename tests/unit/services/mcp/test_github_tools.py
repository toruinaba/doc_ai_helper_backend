"""
Unit tests for GitHub MCP tools integration.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from doc_ai_helper_backend.services.mcp.tools.github_tools import (
    create_github_issue,
    create_github_pull_request,
    check_github_repository_permissions,
)

pytestmark = pytest.mark.asyncio


class TestGitHubMCPTools:
    """Test class for GitHub MCP tools."""

    @patch("doc_ai_helper_backend.services.mcp.tools.github_tools.GitHubClient")
    @pytest.mark.asyncio
    async def test_create_github_issue_success(self, mock_github_client):
        """Test successful GitHub issue creation."""
        # Setup mock GitHub client
        mock_client_instance = AsyncMock()
        mock_github_client.return_value = mock_client_instance

        # Mock repository permissions check
        mock_client_instance.check_repository_permissions.return_value = {
            "issues": True,
            "write": True,
        }

        # Mock issue creation response
        mock_issue_data = {
            "number": 123,
            "html_url": "https://github.com/test/repo/issues/123",
            "url": "https://api.github.com/repos/test/repo/issues/123",
            "title": "Test Issue",
            "body": "This is a test issue",
            "state": "open",
            "labels": [{"name": "bug"}],
            "assignees": [{"login": "testuser"}],
            "created_at": "2024-01-01T00:00:00Z",
        }
        mock_client_instance.create_issue.return_value = mock_issue_data

        # Call the function
        result = await create_github_issue(
            repository="test/repo",
            title="Test Issue",
            description="This is a test issue",
            labels=["bug"],
            assignees=["testuser"],
            github_token="test_token",
        )

        # Parse result
        result_data = json.loads(result)

        # Assertions
        assert result_data["success"] is True
        assert result_data["issue"]["number"] == 123
        assert result_data["issue"]["url"] == "https://github.com/test/repo/issues/123"
        assert result_data["issue"]["title"] == "Test Issue"
        assert result_data["issue"]["labels"] == ["bug"]
        assert result_data["issue"]["assignees"] == ["testuser"]
        assert result_data["issue"]["repository"] == "test/repo"

        # Verify client calls
        mock_client_instance.check_repository_permissions.assert_called_once_with(
            "test/repo"
        )
        mock_client_instance.create_issue.assert_called_once_with(
            repository="test/repo",
            title="Test Issue",
            body="This is a test issue",
            labels=["bug"],
            assignees=["testuser"],
        )

    @patch("doc_ai_helper_backend.services.mcp.tools.github_tools.GitHubClient")
    async def test_create_github_issue_invalid_repository_format(
        self, mock_github_client
    ):
        """Test GitHub issue creation with invalid repository format."""
        # Call the function with invalid repository format
        result = await create_github_issue(
            repository="invalid-repo",
            title="Test Issue",
            description="This is a test issue",
        )

        # Parse result
        result_data = json.loads(result)

        # Assertions
        assert result_data["success"] is False
        assert result_data["error_type"] == "validation_error"
        assert "Invalid repository format" in result_data["error"]

        # Verify GitHub client was not instantiated
        mock_github_client.assert_not_called()

    @patch("doc_ai_helper_backend.services.mcp.tools.github_tools.GitHubClient")
    async def test_create_github_issue_no_permissions(self, mock_github_client):
        """Test GitHub issue creation with insufficient permissions."""
        # Setup mock GitHub client
        mock_client_instance = AsyncMock()
        mock_github_client.return_value = mock_client_instance

        # Mock repository permissions check - no issue permissions
        mock_client_instance.check_repository_permissions.return_value = {
            "issues": False,
            "write": False,
        }

        # Call the function
        result = await create_github_issue(
            repository="test/repo",
            title="Test Issue",
            description="This is a test issue",
        )

        # Parse result
        result_data = json.loads(result)

        # Assertions
        assert result_data["success"] is False
        assert result_data["error_type"] == "permission_error"
        assert "Issues are disabled" in result_data["error"]

        # Verify permission check was called but issue creation was not
        mock_client_instance.check_repository_permissions.assert_called_once_with(
            "test/repo"
        )
        mock_client_instance.create_issue.assert_not_called()

    @patch("doc_ai_helper_backend.services.mcp.tools.github_tools.GitHubClient")
    async def test_create_github_pull_request_success(self, mock_github_client):
        """Test successful GitHub pull request creation."""
        # Setup mock GitHub client
        mock_client_instance = AsyncMock()
        mock_github_client.return_value = mock_client_instance

        # Mock repository permissions check
        mock_client_instance.check_repository_permissions.return_value = {
            "pull_requests": True,
            "write": True,
        }

        # Mock pull request creation response
        mock_pr_data = {
            "number": 456,
            "html_url": "https://github.com/test/repo/pull/456",
            "url": "https://api.github.com/repos/test/repo/pulls/456",
            "title": "Test PR",
            "body": "This is a test PR",
            "state": "open",
            "head": {"ref": "feature/test", "sha": "abc123"},
            "base": {"ref": "main", "sha": "def456"},
            "created_at": "2024-01-01T00:00:00Z",
        }
        mock_client_instance.create_pull_request.return_value = mock_pr_data

        # Call the function
        result = await create_github_pull_request(
            repository="test/repo",
            title="Test PR",
            description="This is a test PR",
            head_branch="feature/test",
            base_branch="main",
            github_token="test_token",
        )

        # Parse result
        result_data = json.loads(result)

        # Assertions
        assert result_data["success"] is True
        assert result_data["pull_request"]["number"] == 456
        assert (
            result_data["pull_request"]["url"]
            == "https://github.com/test/repo/pull/456"
        )
        assert result_data["pull_request"]["title"] == "Test PR"
        assert result_data["pull_request"]["head"]["branch"] == "feature/test"
        assert result_data["pull_request"]["base"]["branch"] == "main"
        assert result_data["pull_request"]["repository"] == "test/repo"

        # Verify client calls
        mock_client_instance.check_repository_permissions.assert_called_once_with(
            "test/repo"
        )
        mock_client_instance.create_pull_request.assert_called_once_with(
            repository="test/repo",
            title="Test PR",
            body="This is a test PR",
            head_branch="feature/test",
            base_branch="main",
        )

    @patch("doc_ai_helper_backend.services.mcp.tools.github_tools.GitHubClient")
    async def test_check_github_repository_permissions_success(
        self, mock_github_client
    ):
        """Test successful GitHub repository permissions check."""
        # Setup mock GitHub client
        mock_client_instance = AsyncMock()
        mock_github_client.return_value = mock_client_instance

        # Mock repository permissions
        mock_permissions = {
            "admin": False,
            "maintain": False,
            "push": True,
            "triage": True,
            "pull": True,
            "issues": True,
            "pull_requests": True,
            "write": True,
        }
        mock_client_instance.check_repository_permissions.return_value = (
            mock_permissions
        )

        # Mock repository info
        mock_repo_info = {
            "name": "repo",
            "full_name": "test/repo",
            "private": False,
            "has_issues": True,
            "has_projects": True,
            "has_wiki": True,
            "default_branch": "main",
        }
        mock_client_instance.get_repository_info.return_value = mock_repo_info

        # Call the function
        result = await check_github_repository_permissions(
            repository="test/repo",
            github_token="test_token",
        )

        # Parse result
        result_data = json.loads(result)

        # Assertions
        assert result_data["success"] is True
        assert result_data["repository"] == "test/repo"
        assert result_data["permissions"] == mock_permissions
        assert result_data["repository_info"]["name"] == "repo"
        assert result_data["repository_info"]["private"] is False
        assert result_data["repository_info"]["has_issues"] is True

        # Verify client calls
        mock_client_instance.check_repository_permissions.assert_called_once_with(
            "test/repo"
        )
        mock_client_instance.get_repository_info.assert_called_once_with("test/repo")

    @patch("doc_ai_helper_backend.services.mcp.tools.github_tools.GitHubClient")
    async def test_github_repository_not_found_error(self, mock_github_client):
        """Test GitHub repository not found error handling."""
        from doc_ai_helper_backend.services.github.exceptions import (
            GitHubRepositoryNotFoundError,
        )

        # Setup mock GitHub client
        mock_client_instance = AsyncMock()
        mock_github_client.return_value = mock_client_instance

        # Mock repository not found error
        mock_client_instance.check_repository_permissions.side_effect = (
            GitHubRepositoryNotFoundError("Repository not found")
        )

        # Call the function
        result = await check_github_repository_permissions(
            repository="nonexistent/repo",
            github_token="test_token",
        )

        # Parse result
        result_data = json.loads(result)

        # Assertions
        assert result_data["success"] is False
        assert result_data["error_type"] == "repository_not_found"
        assert "Repository not found" in result_data["error"]

    @patch("doc_ai_helper_backend.services.mcp.tools.github_tools.GitHubClient")
    async def test_github_permission_error(self, mock_github_client):
        """Test GitHub permission error handling."""
        from doc_ai_helper_backend.services.github.exceptions import (
            GitHubPermissionError,
        )

        # Setup mock GitHub client
        mock_client_instance = AsyncMock()
        mock_github_client.return_value = mock_client_instance

        # Mock permission error
        mock_client_instance.check_repository_permissions.side_effect = (
            GitHubPermissionError("Permission denied")
        )

        # Call the function
        result = await check_github_repository_permissions(
            repository="private/repo",
            github_token="invalid_token",
        )

        # Parse result
        result_data = json.loads(result)

        # Assertions
        assert result_data["success"] is False
        assert result_data["error_type"] == "permission_denied"
        assert "Permission denied" in result_data["error"]

    @patch("doc_ai_helper_backend.services.mcp.tools.github_tools.GitHubClient")
    async def test_github_unexpected_error(self, mock_github_client):
        """Test GitHub unexpected error handling."""
        # Setup mock GitHub client
        mock_client_instance = AsyncMock()
        mock_github_client.return_value = mock_client_instance

        # Mock unexpected error
        mock_client_instance.check_repository_permissions.side_effect = Exception(
            "Unexpected error"
        )

        # Call the function
        result = await check_github_repository_permissions(
            repository="test/repo",
            github_token="test_token",
        )

        # Parse result
        result_data = json.loads(result)

        # Assertions
        assert result_data["success"] is False
        assert result_data["error_type"] == "unexpected_error"
        assert "Unexpected error" in result_data["error"]
