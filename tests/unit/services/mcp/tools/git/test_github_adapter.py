"""
Unit tests for GitHub MCP adapter.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from doc_ai_helper_backend.services.mcp.tools.git.github_adapter import (
    MCPGitHubAdapter,
    MCPGitHubClient,
)
from doc_ai_helper_backend.models.repository_context import (
    RepositoryContext,
    GitService,
)


class TestMCPGitHubClient:
    """Test cases for MCPGitHubClient."""

    def test_init_with_token(self):
        """Test initialization with access token."""
        client = MCPGitHubClient(access_token="test_token")
        assert client.access_token == "test_token"
        assert client.base_url == "https://api.github.com"

    def test_init_with_custom_base_url(self):
        """Test initialization with custom base URL."""
        client = MCPGitHubClient(
            access_token="test_token", base_url="https://github.enterprise.com/api/v3"
        )
        assert client.base_url == "https://github.enterprise.com/api/v3"

    def test_init_without_token_raises_error(self):
        """Test that initialization without token raises GitHubAuthError."""
        from doc_ai_helper_backend.services.github.exceptions import GitHubAuthError

        with pytest.raises(GitHubAuthError):
            MCPGitHubClient()

    @pytest.mark.asyncio
    async def test_create_issue_success(self):
        """Test successful issue creation."""
        client = MCPGitHubClient(access_token="test_token")

        # Mock the GitHub client's create_issue method
        mock_result = {
            "number": 123,
            "title": "Test Issue",
            "html_url": "https://github.com/owner/repo/issues/123",
            "state": "open",
            "created_at": "2024-01-01T00:00:00Z",
        }

        with patch.object(
            client.github_client, "create_issue", return_value=mock_result
        ) as mock_create:
            result = await client.create_issue(
                repository="owner/repo",
                title="Test Issue",
                description="This is a test issue",
                labels=["bug", "enhancement"],
                assignees=["user1"],
            )

            assert result["issue_number"] == 123
            assert result["title"] == "Test Issue"
            assert result["issue_url"] == "https://github.com/owner/repo/issues/123"

            # Verify the GitHub client was called with correct parameters
            mock_create.assert_called_once_with(
                repository="owner/repo",
                title="Test Issue",
                body="This is a test issue",
                labels=["bug", "enhancement"],
                assignees=["user1"],
            )

    @pytest.mark.asyncio
    async def test_create_issue_error(self):
        """Test issue creation with error response."""
        client = MCPGitHubClient(access_token="test_token")

        from doc_ai_helper_backend.services.github.exceptions import GitHubException

        # Mock the GitHub client to raise an exception
        with patch.object(
            client.github_client,
            "create_issue",
            side_effect=GitHubException("API Error"),
        ):
            with pytest.raises(GitHubException):
                await client.create_issue(
                    repository="owner/repo", title="Test Issue", description="Test"
                )

    @pytest.mark.asyncio
    async def test_create_pull_request_success(self):
        """Test successful pull request creation."""
        client = MCPGitHubClient(access_token="test_token")

        # Mock the GitHub client's create_pull_request method
        mock_result = {
            "number": 456,
            "title": "Test PR",
            "html_url": "https://github.com/owner/repo/pull/456",
            "state": "open",
            "head": {"ref": "feature-branch"},
            "base": {"ref": "main"},
            "created_at": "2024-01-01T00:00:00Z",
        }

        with patch.object(
            client.github_client, "create_pull_request", return_value=mock_result
        ) as mock_create:
            result = await client.create_pull_request(
                repository="owner/repo",
                title="Test PR",
                description="This is a test PR",
                head_branch="feature-branch",
                base_branch="main",
            )

            assert result["pr_number"] == 456
            assert result["title"] == "Test PR"
            assert result["pr_url"] == "https://github.com/owner/repo/pull/456"

            # Verify the GitHub client was called with correct parameters
            mock_create.assert_called_once_with(
                repository="owner/repo",
                title="Test PR",
                body="This is a test PR",
                head="feature-branch",
                base="main",
            )

    @pytest.mark.asyncio
    async def test_check_repository_permissions_success(self):
        """Test successful repository permissions check."""
        client = MCPGitHubClient(access_token="test_token")

        # Mock the GitHub client's check_repository_permissions method
        mock_permissions = {"admin": True, "push": True, "pull": True}

        with patch.object(
            client.github_client,
            "check_repository_permissions",
            return_value=mock_permissions,
        ) as mock_check:
            result = await client.check_repository_permissions(repository="owner/repo")

            assert result["permissions"]["admin"] is True
            assert result["permissions"]["push"] is True
            assert result["permissions"]["pull"] is True
            assert result["can_admin"] is True
            assert result["can_write"] is True
            assert result["can_read"] is True

            # Verify the GitHub client was called with correct parameters
            mock_check.assert_called_once_with("owner/repo")


class TestMCPGitHubAdapter:
    """Test cases for MCPGitHubAdapter."""

    def test_init_with_config(self):
        """Test initialization with configuration."""
        config = {
            "access_token": "test_token",
            "default_labels": ["bug", "enhancement"],
        }
        adapter = MCPGitHubAdapter(config)
        assert adapter.config == config
        assert adapter.client.access_token == "test_token"

    def test_init_without_access_token_raises_error(self):
        """Test that initialization without access token raises ValueError."""
        with pytest.raises(ValueError, match="access_token is required"):
            MCPGitHubAdapter({})

    @pytest.mark.asyncio
    async def test_create_issue_with_repository_context(self):
        """Test issue creation with repository context."""
        config = {"access_token": "test_token", "default_labels": ["bug"]}
        adapter = MCPGitHubAdapter(config)

        # Mock the client
        adapter.client.create_issue = AsyncMock(
            return_value={
                "issue_number": 123,
                "title": "Test Issue",
                "issue_url": "https://github.com/owner/repo/issues/123",
            }
        )

        repo_context = RepositoryContext(
            owner="owner", repo="repo", service=GitService.GITHUB, ref="main"
        )

        result = await adapter.create_issue(
            title="Test Issue",
            description="This is a test issue",
            labels=["enhancement"],
            assignees=["user1"],
            repository_context=repo_context.model_dump(),
        )

        # Parse JSON response
        import json

        result_data = json.loads(result)

        assert result_data["success"] is True
        assert "Issue created successfully" in result_data["message"]
        assert result_data["data"]["issue_number"] == 123
        assert (
            "https://github.com/owner/repo/issues/123"
            in result_data["data"]["issue_url"]
        )

        # Verify client was called with correct parameters
        adapter.client.create_issue.assert_called_once_with(
            repository="owner/repo",
            title="Test Issue",
            description="This is a test issue",
            labels=["enhancement"],
            assignees=["user1"],
        )

    @pytest.mark.asyncio
    async def test_create_issue_without_repository_context_returns_error(self):
        """Test that issue creation without repository context returns error response."""
        config = {"access_token": "test_token"}
        adapter = MCPGitHubAdapter(config)

        result = await adapter.create_issue(
            title="Test Issue", description="This is a test issue"
        )

        # Parse JSON response
        import json

        result_data = json.loads(result)
        assert result_data["success"] is False
        assert "Repository context is required" in result_data["error"]

    @pytest.mark.asyncio
    async def test_create_pull_request_with_repository_context(self):
        """Test pull request creation with repository context."""
        config = {"access_token": "test_token"}
        adapter = MCPGitHubAdapter(config)

        # Mock the client
        adapter.client.create_pull_request = AsyncMock(
            return_value={
                "pr_number": 456,
                "title": "Test PR",
                "pr_url": "https://github.com/owner/repo/pull/456",
            }
        )

        repo_context = RepositoryContext(
            owner="owner", repo="repo", service=GitService.GITHUB, ref="main"
        )

        result = await adapter.create_pull_request(
            title="Test PR",
            description="This is a test PR",
            head_branch="feature-branch",
            base_branch="main",
            repository_context=repo_context.model_dump(),
        )

        # Parse JSON response
        import json

        result_data = json.loads(result)

        assert result_data["success"] is True
        assert "Pull request created successfully" in result_data["message"]
        assert result_data["data"]["pr_number"] == 456
        assert "https://github.com/owner/repo/pull/456" in result_data["data"]["pr_url"]

        # Verify client was called with correct parameters
        adapter.client.create_pull_request.assert_called_once_with(
            repository="owner/repo",
            title="Test PR",
            description="This is a test PR",
            head_branch="feature-branch",
            base_branch="main",
        )

    @pytest.mark.asyncio
    async def test_check_repository_permissions_with_repository_context(self):
        """Test repository permissions check with repository context."""
        config = {"access_token": "test_token"}
        adapter = MCPGitHubAdapter(config)

        # Mock the client
        adapter.client.check_repository_permissions = AsyncMock(
            return_value={
                "repository": "owner/repo",
                "permissions": {"admin": True, "push": True, "pull": True},
                "can_read": True,
                "can_write": True,
                "can_admin": True,
            }
        )

        repo_context = RepositoryContext(
            owner="owner", repo="repo", service=GitService.GITHUB, ref="main"
        )

        result = await adapter.check_repository_permissions(
            repository_context=repo_context.model_dump()
        )

        # Parse JSON response
        import json

        result_data = json.loads(result)

        assert result_data["success"] is True
        assert "Repository permissions retrieved" in result_data["message"]
        assert result_data["permissions"]["permissions"]["admin"] is True
        assert result_data["permissions"]["permissions"]["push"] is True
        assert result_data["permissions"]["permissions"]["pull"] is True

        # Verify client was called with correct parameters
        adapter.client.check_repository_permissions.assert_called_once_with(
            repository="owner/repo"
        )

    @pytest.mark.asyncio
    async def test_handle_client_error(self):
        """Test error handling when client raises exception."""
        config = {"access_token": "test_token"}
        adapter = MCPGitHubAdapter(config)

        # Mock the client to raise an exception
        adapter.client.create_issue = AsyncMock(side_effect=Exception("API Error"))

        repo_context = RepositoryContext(
            owner="owner", repo="repo", service=GitService.GITHUB, ref="main"
        )

        result = await adapter.create_issue(
            title="Test Issue",
            description="This is a test issue",
            repository_context=repo_context.model_dump(),
        )

        # Parse JSON response
        import json

        result_data = json.loads(result)

        assert result_data["success"] is False
        assert "API Error" in result_data["error"]
