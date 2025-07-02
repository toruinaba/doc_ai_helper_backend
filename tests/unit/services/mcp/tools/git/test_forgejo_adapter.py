"""
Unit tests for Forgejo MCP adapter.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from doc_ai_helper_backend.services.mcp.tools.git.forgejo_adapter import (
    MCPForgejoAdapter,
    MCPForgejoClient,
)
from doc_ai_helper_backend.models.repository_context import RepositoryContext


class TestMCPForgejoClient:
    """Test cases for MCPForgejoClient."""

    def test_init_with_token(self):
        """Test initialization with access token."""
        client = MCPForgejoClient(
            base_url="https://forgejo.example.com", access_token="test_token"
        )
        assert client.access_token == "test_token"
        assert client.base_url == "https://forgejo.example.com"
        assert client.username is None
        assert client.password is None

    def test_init_with_username_password(self):
        """Test initialization with username and password."""
        client = MCPForgejoClient(
            base_url="https://forgejo.example.com",
            username="testuser",
            password="testpass",
        )
        assert client.username == "testuser"
        assert client.password == "testpass"
        assert client.access_token is None

    def test_init_without_auth_raises_error(self):
        """Test that initialization without auth raises ValueError."""
        with pytest.raises(
            ValueError, match="Either access_token or username/password is required"
        ):
            MCPForgejoClient(base_url="https://forgejo.example.com")

    def test_init_without_base_url_raises_error(self):
        """Test that initialization without base_url raises ValueError."""
        with pytest.raises(ValueError, match="base_url is required"):
            MCPForgejoClient(access_token="test_token")

    @pytest.mark.asyncio
    async def test_create_issue_success_with_token(self):
        """Test successful issue creation with access token."""
        client = MCPForgejoClient(
            base_url="https://forgejo.example.com", access_token="test_token"
        )

        # Mock the HTTP client
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "number": 123,
            "title": "Test Issue",
            "html_url": "https://forgejo.example.com/owner/repo/issues/123",
            "state": "open",
        }

        with patch.object(client, "_make_request", return_value=mock_response):
            result = await client.create_issue(
                owner="owner",
                repo="repo",
                title="Test Issue",
                body="This is a test issue",
                labels=["bug", "enhancement"],
                assignees=["user1"],
            )

            assert result["number"] == 123
            assert result["title"] == "Test Issue"
            assert (
                result["html_url"]
                == "https://forgejo.example.com/owner/repo/issues/123"
            )

    @pytest.mark.asyncio
    async def test_create_issue_success_with_username_password(self):
        """Test successful issue creation with username/password."""
        client = MCPForgejoClient(
            base_url="https://forgejo.example.com",
            username="testuser",
            password="testpass",
        )

        # Mock the HTTP client
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "number": 123,
            "title": "Test Issue",
            "html_url": "https://forgejo.example.com/owner/repo/issues/123",
            "state": "open",
        }

        with patch.object(client, "_make_request", return_value=mock_response):
            result = await client.create_issue(
                owner="owner",
                repo="repo",
                title="Test Issue",
                body="This is a test issue",
                labels=["bug"],
            )

            assert result["number"] == 123
            assert result["title"] == "Test Issue"

    @pytest.mark.asyncio
    async def test_create_issue_error(self):
        """Test issue creation with error response."""
        client = MCPForgejoClient(
            base_url="https://forgejo.example.com", access_token="test_token"
        )

        # Mock the HTTP client to return error
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "Bad Request"}

        with patch.object(client, "_make_request", return_value=mock_response):
            with pytest.raises(Exception, match="HTTP 400"):
                await client.create_issue(
                    owner="owner", repo="repo", title="Test Issue", body="Test"
                )

    @pytest.mark.asyncio
    async def test_create_pull_request_success(self):
        """Test successful pull request creation."""
        client = MCPForgejoClient(
            base_url="https://forgejo.example.com", access_token="test_token"
        )

        # Mock the HTTP client
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "number": 456,
            "title": "Test PR",
            "html_url": "https://forgejo.example.com/owner/repo/pulls/456",
            "state": "open",
        }

        with patch.object(client, "_make_request", return_value=mock_response):
            result = await client.create_pull_request(
                owner="owner",
                repo="repo",
                title="Test PR",
                body="This is a test PR",
                head="feature-branch",
                base="main",
            )

            assert result["number"] == 456
            assert result["title"] == "Test PR"
            assert (
                result["html_url"] == "https://forgejo.example.com/owner/repo/pulls/456"
            )

    @pytest.mark.asyncio
    async def test_check_repository_permissions_success(self):
        """Test successful repository permissions check."""
        client = MCPForgejoClient(
            base_url="https://forgejo.example.com", access_token="test_token"
        )

        # Mock the HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "permissions": {"admin": True, "push": True, "pull": True}
        }

        with patch.object(client, "_make_request", return_value=mock_response):
            result = await client.check_repository_permissions(
                owner="owner", repo="repo"
            )

            assert result["permissions"]["admin"] is True
            assert result["permissions"]["push"] is True
            assert result["permissions"]["pull"] is True


class TestMCPForgejoAdapter:
    """Test cases for MCPForgejoAdapter."""

    def test_init_with_token_config(self):
        """Test initialization with token configuration."""
        config = {
            "base_url": "https://forgejo.example.com",
            "access_token": "test_token",
            "default_labels": ["bug", "enhancement"],
        }
        adapter = MCPForgejoAdapter(config)
        assert adapter.config == config
        assert adapter.client.access_token == "test_token"
        assert adapter.client.base_url == "https://forgejo.example.com"

    def test_init_with_username_password_config(self):
        """Test initialization with username/password configuration."""
        config = {
            "base_url": "https://forgejo.example.com",
            "username": "testuser",
            "password": "testpass",
            "default_labels": ["bug"],
        }
        adapter = MCPForgejoAdapter(config)
        assert adapter.config == config
        assert adapter.client.username == "testuser"
        assert adapter.client.password == "testpass"

    def test_init_without_base_url_raises_error(self):
        """Test that initialization without base_url raises ValueError."""
        with pytest.raises(ValueError, match="base_url is required"):
            MCPForgejoAdapter({"access_token": "test_token"})

    def test_init_without_auth_raises_error(self):
        """Test that initialization without auth raises ValueError."""
        with pytest.raises(
            ValueError, match="Either access_token or username/password is required"
        ):
            MCPForgejoAdapter({"base_url": "https://forgejo.example.com"})

    @pytest.mark.asyncio
    async def test_create_issue_with_repository_context(self):
        """Test issue creation with repository context."""
        config = {
            "base_url": "https://forgejo.example.com",
            "access_token": "test_token",
            "default_labels": ["bug"],
        }
        adapter = MCPForgejoAdapter(config)

        # Mock the client
        adapter.client.create_issue = AsyncMock(
            return_value={
                "number": 123,
                "title": "Test Issue",
                "html_url": "https://forgejo.example.com/owner/repo/issues/123",
            }
        )

        repo_context = RepositoryContext(
            owner="owner", repo="repo", service="forgejo", ref="main", path=""
        )

        result = await adapter.create_issue(
            title="Test Issue",
            description="This is a test issue",
            labels=["enhancement"],
            assignees=["user1"],
            repository_context=repo_context,
        )

        assert "Issue created successfully" in result
        assert "#123" in result
        assert "https://forgejo.example.com/owner/repo/issues/123" in result

        # Verify client was called with correct parameters
        adapter.client.create_issue.assert_called_once_with(
            owner="owner",
            repo="repo",
            title="Test Issue",
            body="This is a test issue",
            labels=["bug", "enhancement"],  # Includes default labels
            assignees=["user1"],
        )

    @pytest.mark.asyncio
    async def test_create_issue_without_repository_context_raises_error(self):
        """Test that issue creation without repository context raises ValueError."""
        config = {
            "base_url": "https://forgejo.example.com",
            "access_token": "test_token",
        }
        adapter = MCPForgejoAdapter(config)

        with pytest.raises(ValueError, match="repository_context is required"):
            await adapter.create_issue(
                title="Test Issue", description="This is a test issue"
            )

    @pytest.mark.asyncio
    async def test_create_pull_request_with_repository_context(self):
        """Test pull request creation with repository context."""
        config = {
            "base_url": "https://forgejo.example.com",
            "access_token": "test_token",
        }
        adapter = MCPForgejoAdapter(config)

        # Mock the client
        adapter.client.create_pull_request = AsyncMock(
            return_value={
                "number": 456,
                "title": "Test PR",
                "html_url": "https://forgejo.example.com/owner/repo/pulls/456",
            }
        )

        repo_context = RepositoryContext(
            owner="owner", repo="repo", service="forgejo", ref="main", path=""
        )

        result = await adapter.create_pull_request(
            title="Test PR",
            description="This is a test PR",
            head_branch="feature-branch",
            base_branch="main",
            repository_context=repo_context,
        )

        assert "Pull request created successfully" in result
        assert "#456" in result
        assert "https://forgejo.example.com/owner/repo/pulls/456" in result

        # Verify client was called with correct parameters
        adapter.client.create_pull_request.assert_called_once_with(
            owner="owner",
            repo="repo",
            title="Test PR",
            body="This is a test PR",
            head="feature-branch",
            base="main",
        )

    @pytest.mark.asyncio
    async def test_check_repository_permissions_with_repository_context(self):
        """Test repository permissions check with repository context."""
        config = {
            "base_url": "https://forgejo.example.com",
            "access_token": "test_token",
        }
        adapter = MCPForgejoAdapter(config)

        # Mock the client
        adapter.client.check_repository_permissions = AsyncMock(
            return_value={"permissions": {"admin": True, "push": True, "pull": True}}
        )

        repo_context = RepositoryContext(
            owner="owner", repo="repo", service="forgejo", ref="main", path=""
        )

        result = await adapter.check_repository_permissions(
            repository_context=repo_context
        )

        assert "Repository permissions" in result
        assert "admin: True" in result
        assert "push: True" in result
        assert "pull: True" in result

        # Verify client was called with correct parameters
        adapter.client.check_repository_permissions.assert_called_once_with(
            owner="owner", repo="repo"
        )

    @pytest.mark.asyncio
    async def test_handle_client_error(self):
        """Test error handling when client raises exception."""
        config = {
            "base_url": "https://forgejo.example.com",
            "access_token": "test_token",
        }
        adapter = MCPForgejoAdapter(config)

        # Mock the client to raise an exception
        adapter.client.create_issue = AsyncMock(side_effect=Exception("API Error"))

        repo_context = RepositoryContext(
            owner="owner", repo="repo", service="forgejo", ref="main", path=""
        )

        result = await adapter.create_issue(
            title="Test Issue",
            description="This is a test issue",
            repository_context=repo_context,
        )

        assert "Failed to create issue" in result
        assert "API Error" in result
