"""
Unit tests for Forgejo MCP adapter.
"""

import json
import pytest
from unittest.mock import Mock, AsyncMock, patch
from doc_ai_helper_backend.services.mcp.tools.git.forgejo_adapter import (
    MCPForgejoAdapter,
    MCPForgejoClient,
)
from doc_ai_helper_backend.models.repository_context import (
    RepositoryContext,
    GitService,
)


class TestMCPForgejoAdapter:
    """Test suite for MCPForgejoAdapter."""

    def test_init_with_token_config(self):
        """Test initialization with token configuration."""
        config = {
            "base_url": "https://forgejo.example.com",
            "access_token": "test_token",
            "default_labels": ["bug"],
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
        }
        adapter = MCPForgejoAdapter(config)

        repo_context = RepositoryContext(
            service=GitService.FORGEJO,
            owner="test_owner",
            repo="test_repo",
            ref="main",
            base_url="https://forgejo.example.com",
        )

        # Mock the client's create_issue method
        with patch.object(adapter.client, "create_issue") as mock_create:
            mock_create.return_value = {
                "number": 123,
                "title": "Test Issue",
                "html_url": "https://forgejo.example.com/test_owner/test_repo/issues/123",
            }

            result = await adapter.create_issue(
                title="Test Issue",
                description="This is a test issue",
                labels=["enhancement"],
                assignees=["user1"],
                repository_context=repo_context.dict(),
            )

            assert "Issue created successfully" in result
            assert '"number": 123' in result
            assert (
                "https://forgejo.example.com/test_owner/test_repo/issues/123" in result
            )

    @pytest.mark.asyncio
    async def test_create_issue_without_repository_context_returns_error(self):
        """Test that creating issue without repository context returns error."""
        config = {
            "base_url": "https://forgejo.example.com",
            "access_token": "test_token",
        }
        adapter = MCPForgejoAdapter(config)

        result = await adapter.create_issue(
            title="Test Issue", description="This is a test issue"
        )

        # Should return JSON error response
        result_data = json.loads(result)
        assert result_data["success"] is False
        assert "Repository context is required" in result_data["error"]


class TestMCPForgejoClient:
    """Test suite for MCPForgejoClient."""

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
        """Test that initialization without auth logs warning."""
        # This should not raise an error but log a warning
        client = MCPForgejoClient(base_url="https://forgejo.example.com")
        assert client.access_token is None
        assert client.username is None

    def test_init_without_base_url_raises_error(self):
        """Test that initialization without base_url raises error."""
        with pytest.raises(TypeError):
            MCPForgejoClient(access_token="test_token")

    @pytest.mark.asyncio
    async def test_create_issue_success_with_token(self):
        """Test successful issue creation with token."""
        client = MCPForgejoClient(
            base_url="https://forgejo.example.com", access_token="test_token"
        )

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "number": 123,
            "title": "Test Issue",
            "html_url": "https://forgejo.example.com/owner/repo/issues/123",
            "state": "open",
            "created_at": "2024-01-01T00:00:00Z",
        }

        # Mock the httpx client directly
        with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
            result = await client.create_issue(
                repository="owner/repo",
                title="Test Issue",
                description="This is a test issue",
                labels=["bug", "enhancement"],
                assignees=["user1"],
            )

            assert result["issue_number"] == 123
            assert result["title"] == "Test Issue"
            assert (
                result["issue_url"]
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

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "number": 456,
            "title": "Test Issue",
            "html_url": "https://forgejo.example.com/owner/repo/issues/456",
            "state": "open",
            "created_at": "2024-01-01T00:00:00Z",
        }

        # Mock the httpx client directly
        with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
            result = await client.create_issue(
                repository="owner/repo",
                title="Test Issue",
                description="This is a test issue",
                labels=["bug"],
                assignees=["user2"],
            )

            assert result["issue_number"] == 456

    @pytest.mark.asyncio
    async def test_create_issue_error(self):
        """Test issue creation error handling."""
        client = MCPForgejoClient(
            base_url="https://forgejo.example.com", access_token="test_token"
        )

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        # Mock the httpx client directly
        with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
            with pytest.raises(Exception):
                await client.create_issue(
                    repository="owner/repo", title="Test Issue", description="Test"
                )

    @pytest.mark.asyncio
    async def test_create_pull_request_success(self):
        """Test successful pull request creation."""
        client = MCPForgejoClient(
            base_url="https://forgejo.example.com", access_token="test_token"
        )

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "number": 789,
            "title": "Test PR",
            "html_url": "https://forgejo.example.com/owner/repo/pulls/789",
            "state": "open",
            "created_at": "2024-01-01T00:00:00Z",
        }

        # Mock the httpx client directly
        with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
            result = await client.create_pull_request(
                repository="owner/repo",
                title="Test PR",
                description="This is a test PR",
                head_branch="feature",
                base_branch="main",
            )

            assert result["pr_number"] == 789
            assert result["title"] == "Test PR"

    @pytest.mark.asyncio
    async def test_check_repository_permissions_success(self):
        """Test successful repository permissions check."""
        client = MCPForgejoClient(
            base_url="https://forgejo.example.com", access_token="test_token"
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "permissions": {
                "admin": False,
                "push": True,
                "pull": True,
            }
        }

        # Mock the httpx client directly
        with patch("httpx.AsyncClient.get", return_value=mock_response) as mock_get:
            result = await client.check_repository_permissions(repository="owner/repo")

            assert result["permissions"]["push"] is True
            assert result["permissions"]["pull"] is True
