"""Tests for GitHub MCP tools."""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from doc_ai_helper_backend.services.mcp.tools.github_tools import (
    create_github_issue,
    create_github_pull_request,
    check_github_repository_permissions,
)
from doc_ai_helper_backend.services.github.exceptions import (
    GitHubAPIError,
    GitHubAuthError,
    GitHubRepositoryNotFoundError,
    GitHubPermissionError,
)


class TestGitHubMCPTools:
    """Test cases for GitHub MCP tools."""

    @pytest.mark.asyncio
    @patch("doc_ai_helper_backend.services.mcp.tools.github_tools.GitHubClient")
    async def test_create_github_issue_success(self, mock_client_class):
        """Test successful issue creation."""
        # Setup mock client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        # Mock permissions check
        mock_client.check_repository_permissions.return_value = {
            "issues": True,
            "write": True,
        }

        # Mock issue creation
        mock_client.create_issue.return_value = {
            "number": 123,
            "html_url": "https://github.com/owner/repo/issues/123",
            "url": "https://api.github.com/repos/owner/repo/issues/123",
            "title": "Test Issue",
            "body": "Test description",
            "state": "open",
            "labels": [{"name": "bug"}],
            "assignees": [{"login": "user1"}],
            "created_at": "2025-06-23T12:00:00Z",
        }

        # Call function
        result_json = await create_github_issue(
            repository="owner/repo",
            title="Test Issue",
            description="Test description",
            labels=["bug"],
            assignees=["user1"],
        )

        # Parse result
        result = json.loads(result_json)

        # Assertions
        assert result["success"] is True
        assert result["issue"]["number"] == 123
        assert result["issue"]["url"] == "https://github.com/owner/repo/issues/123"
        assert result["issue"]["title"] == "Test Issue"
        assert result["issue"]["labels"] == ["bug"]
        assert result["issue"]["assignees"] == ["user1"]

        # Verify method calls
        mock_client.check_repository_permissions.assert_called_once_with("owner/repo")
        mock_client.create_issue.assert_called_once_with(
            repository="owner/repo",
            title="Test Issue",
            body="Test description",
            labels=["bug"],
            assignees=["user1"],
        )

    @pytest.mark.asyncio
    @patch("doc_ai_helper_backend.services.mcp.tools.github_tools.GitHubClient")
    async def test_create_github_issue_invalid_repository(self, mock_client_class):
        """Test issue creation with invalid repository format."""
        result_json = await create_github_issue(
            repository="invalid-repo",
            title="Test Issue",
            description="Test description",
        )

        result = json.loads(result_json)

        assert result["success"] is False
        assert "Invalid repository format" in result["error"]
        assert result["error_type"] == "validation_error"

    @pytest.mark.asyncio
    @patch("doc_ai_helper_backend.services.mcp.tools.github_tools.GitHubClient")
    async def test_create_github_issue_no_issues_permission(self, mock_client_class):
        """Test issue creation when issues are disabled."""
        # Setup mock client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        # Mock permissions check - issues disabled
        mock_client.check_repository_permissions.return_value = {
            "issues": False,
            "write": True,
        }

        result_json = await create_github_issue(
            repository="owner/repo",
            title="Test Issue",
            description="Test description",
        )

        result = json.loads(result_json)

        assert result["success"] is False
        assert "Issues are disabled" in result["error"]
        assert result["error_type"] == "permission_error"

    @pytest.mark.asyncio
    @patch("doc_ai_helper_backend.services.mcp.tools.github_tools.GitHubClient")
    async def test_create_github_issue_repository_not_found(self, mock_client_class):
        """Test issue creation when repository is not found."""
        # Setup mock client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        # Mock repository not found
        mock_client.check_repository_permissions.side_effect = (
            GitHubRepositoryNotFoundError("owner/nonexistent")
        )

        result_json = await create_github_issue(
            repository="owner/nonexistent",
            title="Test Issue",
            description="Test description",
        )

        result = json.loads(result_json)

        assert result["success"] is False
        assert "Repository not found" in result["error"]
        assert result["error_type"] == "repository_not_found"

    @pytest.mark.asyncio
    @patch("doc_ai_helper_backend.services.mcp.tools.github_tools.GitHubClient")
    async def test_create_github_pull_request_success(self, mock_client_class):
        """Test successful pull request creation."""
        # Setup mock client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        # Mock permissions check
        mock_client.check_repository_permissions.return_value = {
            "pull_requests": True,
        }

        # Mock PR creation
        mock_client.create_pull_request.return_value = {
            "number": 456,
            "html_url": "https://github.com/owner/repo/pull/456",
            "url": "https://api.github.com/repos/owner/repo/pulls/456",
            "title": "Test PR",
            "body": "Test PR description",
            "state": "open",
            "head": {"ref": "feature-branch", "sha": "abc123"},
            "base": {"ref": "main", "sha": "def456"},
            "created_at": "2025-06-23T12:00:00Z",
        }

        # Call function
        result_json = await create_github_pull_request(
            repository="owner/repo",
            title="Test PR",
            description="Test PR description",
            head_branch="feature-branch",
            base_branch="main",
        )

        # Parse result
        result = json.loads(result_json)

        # Assertions
        assert result["success"] is True
        assert result["pull_request"]["number"] == 456
        assert result["pull_request"]["url"] == "https://github.com/owner/repo/pull/456"
        assert result["pull_request"]["title"] == "Test PR"
        assert result["pull_request"]["head"]["branch"] == "feature-branch"
        assert result["pull_request"]["base"]["branch"] == "main"

    @pytest.mark.asyncio
    @patch("doc_ai_helper_backend.services.mcp.tools.github_tools.GitHubClient")
    async def test_check_github_repository_permissions_success(self, mock_client_class):
        """Test successful repository permissions check."""
        # Setup mock client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        # Mock permissions check
        mock_client.check_repository_permissions.return_value = {
            "read": True,
            "write": False,
            "admin": False,
            "issues": True,
            "pull_requests": True,
        }

        # Mock repository info
        mock_client.get_repository_info.return_value = {
            "name": "repo",
            "full_name": "owner/repo",
            "private": False,
            "has_issues": True,
            "has_projects": True,
            "has_wiki": False,
            "default_branch": "main",
        }

        # Call function
        result_json = await check_github_repository_permissions(
            repository="owner/repo",
        )

        # Parse result
        result = json.loads(result_json)

        # Assertions
        assert result["success"] is True
        assert result["repository"] == "owner/repo"
        assert result["permissions"]["read"] is True
        assert result["permissions"]["write"] is False
        assert result["permissions"]["admin"] is False
        assert result["permissions"]["issues"] is True
        assert result["repository_info"]["name"] == "repo"
        assert result["repository_info"]["default_branch"] == "main"

    @pytest.mark.asyncio
    @patch("doc_ai_helper_backend.services.mcp.tools.github_tools.GitHubClient")
    async def test_github_tools_auth_error_handling(self, mock_client_class):
        """Test handling of authentication errors."""
        # Setup mock client
        mock_client = AsyncMock()
        mock_client_class.side_effect = GitHubAuthError("Invalid token")

        # Test issue creation
        result_json = await create_github_issue(
            repository="owner/repo",
            title="Test Issue",
            description="Test description",
        )

        result = json.loads(result_json)

        assert result["success"] is False
        assert "GitHub API error" in result["error"]
        assert result["error_type"] == "github_api_error"

    @pytest.mark.asyncio
    @patch("doc_ai_helper_backend.services.mcp.tools.github_tools.GitHubClient")
    async def test_github_tools_general_error_handling(self, mock_client_class):
        """Test handling of general errors."""
        # Setup mock client to raise unexpected error
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.check_repository_permissions.side_effect = Exception(
            "Unexpected error"
        )

        # Test issue creation
        result_json = await create_github_issue(
            repository="owner/repo",
            title="Test Issue",
            description="Test description",
        )

        result = json.loads(result_json)

        assert result["success"] is False
        assert "Unexpected error" in result["error"]
        assert result["error_type"] == "unexpected_error"
