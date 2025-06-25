"""
Test secure GitHub tools with repository context validation.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch

from doc_ai_helper_backend.services.mcp.tools.github_tools import (
    create_github_issue,
    create_github_pull_request,
    _validate_repository_access,
    RepositoryAccessError,
)
from doc_ai_helper_backend.models.repository_context import RepositoryContext


class TestRepositoryAccessValidation:
    """Test repository access validation."""

    def test_validate_repository_access_success(self):
        """Test successful repository access validation."""
        repo_context = RepositoryContext(
            service="github", owner="test-owner", repo="test-repo", ref="main"
        )

        # Should not raise exception for matching repository
        _validate_repository_access("test-owner/test-repo", repo_context)

    def test_validate_repository_access_failure(self):
        """Test repository access validation failure."""
        repo_context = RepositoryContext(
            service="github", owner="test-owner", repo="test-repo", ref="main"
        )

        # Should raise exception for different repository
        with pytest.raises(RepositoryAccessError):
            _validate_repository_access("other-owner/other-repo", repo_context)

    def test_validate_repository_access_no_context(self):
        """Test repository access validation with no context (should allow)."""
        # Should not raise exception when no context provided (backward compatibility)
        _validate_repository_access("any-owner/any-repo", None)


class TestSecureGitHubIssue:
    """Test secure GitHub issue creation."""

    @pytest.mark.asyncio
    async def test_create_github_issue_success(self):
        """Test successful secure GitHub issue creation."""
        repository_context = {
            "service": "github",
            "owner": "test-owner",
            "repo": "test-repo",
            "ref": "main",
        }

        mock_issue_data = {
            "number": 123,
            "html_url": "https://github.com/test-owner/test-repo/issues/123",
            "url": "https://api.github.com/repos/test-owner/test-repo/issues/123",
            "title": "Test Issue",
            "body": "Test Description",
            "state": "open",
            "labels": [],
            "assignees": [],
            "created_at": "2024-01-01T00:00:00Z",
        }

        with patch(
            "doc_ai_helper_backend.services.mcp.tools.secure_github_tools.GitHubClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.check_repository_permissions.return_value = {
                "issues": True,
                "write": True,
            }
            mock_client.create_issue.return_value = mock_issue_data

            result = await create_github_issue(
                title="Test Issue",
                description="Test Description",
                repository_context=repository_context,
            )

            result_data = json.loads(result)
            assert result_data["success"] is True
            assert result_data["issue"]["number"] == 123
            assert result_data["issue"]["repository"] == "test-owner/test-repo"
            assert result_data["issue"]["context_validated"] is True

            # Verify GitHubClient was called with correct repository
            mock_client.create_issue.assert_called_once_with(
                repository="test-owner/test-repo",
                title="Test Issue",
                body="Test Description",
                labels=[],
                assignees=[],
            )

    @pytest.mark.asyncio
    async def test_create_github_issue_no_context(self):
        """Test secure GitHub issue creation without repository context."""
        result = await create_github_issue(
            title="Test Issue", description="Test Description", repository_context=None
        )

        result_data = json.loads(result)
        assert result_data["success"] is False
        assert result_data["error_type"] == "context_required"
        assert "No repository context provided" in result_data["error"]

    @pytest.mark.asyncio
    async def test_create_github_issue_permission_denied(self):
        """Test secure GitHub issue creation with permission denied."""
        repository_context = {
            "service": "github",
            "owner": "test-owner",
            "repo": "test-repo",
            "ref": "main",
        }

        with patch(
            "doc_ai_helper_backend.services.mcp.tools.secure_github_tools.GitHubClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.check_repository_permissions.return_value = {
                "issues": False,
                "write": False,
            }

            result = await create_github_issue(
                title="Test Issue",
                description="Test Description",
                repository_context=repository_context,
            )

            result_data = json.loads(result)
            assert result_data["success"] is False
            assert result_data["error_type"] == "permission_error"
            assert "Issues are disabled" in result_data["error"]


class TestSecureGitHubPullRequest:
    """Test secure GitHub pull request creation."""

    @pytest.mark.asyncio
    async def test_create_github_pull_request_success(self):
        """Test successful secure GitHub pull request creation."""
        repository_context = {
            "service": "github",
            "owner": "test-owner",
            "repo": "test-repo",
            "ref": "main",
        }

        mock_pr_data = {
            "number": 456,
            "html_url": "https://github.com/test-owner/test-repo/pull/456",
            "url": "https://api.github.com/repos/test-owner/test-repo/pulls/456",
            "title": "Test PR",
            "body": "Test PR Description",
            "state": "open",
            "head": {"ref": "feature-branch", "sha": "abc123"},
            "base": {"ref": "main", "sha": "def456"},
            "created_at": "2024-01-01T00:00:00Z",
        }

        with patch(
            "doc_ai_helper_backend.services.mcp.tools.secure_github_tools.GitHubClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.check_repository_permissions.return_value = {
                "pull_requests": True,
                "write": True,
            }
            mock_client.create_pull_request.return_value = mock_pr_data

            result = await create_github_pull_request(
                title="Test PR",
                description="Test PR Description",
                head_branch="feature-branch",
                base_branch="main",
                repository_context=repository_context,
            )

            result_data = json.loads(result)
            assert result_data["success"] is True
            assert result_data["pull_request"]["number"] == 456
            assert result_data["pull_request"]["repository"] == "test-owner/test-repo"
            assert result_data["pull_request"]["context_validated"] is True

            # Verify GitHubClient was called with correct repository
            mock_client.create_pull_request.assert_called_once_with(
                repository="test-owner/test-repo",
                title="Test PR",
                body="Test PR Description",
                head_branch="feature-branch",
                base_branch="main",
            )

    @pytest.mark.asyncio
    async def test_create_github_pull_request_no_context(self):
        """Test secure GitHub pull request creation without repository context."""
        result = await create_github_pull_request(
            title="Test PR",
            description="Test PR Description",
            head_branch="feature-branch",
            repository_context=None,
        )

        result_data = json.loads(result)
        assert result_data["success"] is False
        assert result_data["error_type"] == "context_required"
        assert "No repository context provided" in result_data["error"]
