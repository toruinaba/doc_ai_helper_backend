"""Tests for GitHub client."""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from doc_ai_helper_backend.services.mcp.tools.git.github_client import GitHubClient
from doc_ai_helper_backend.core.exceptions import (
    GitHubAPIError,
    GitHubAuthError,
    GitHubRateLimitError,
    GitHubRepositoryNotFoundError,
    GitHubPermissionError,
)


class TestGitHubClient:
    """Test cases for GitHubClient."""

    @patch.dict("os.environ", {"GITHUB_TOKEN": "test_token"})
    def test_init_default(self):
        """Test client initialization with default values."""
        client = GitHubClient()
        assert client.base_url == "https://api.github.com"
        assert client.timeout == 30.0
        assert client.auth_manager.token == "test_token"

    def test_init_custom(self):
        """Test client initialization with custom values."""
        client = GitHubClient(
            token="custom_token",
            base_url="https://api.github.enterprise.com",
            timeout=60.0,
        )
        assert client.base_url == "https://api.github.enterprise.com"
        assert client.timeout == 60.0
        assert client.auth_manager.token == "custom_token"

    def test_parse_repository_valid(self):
        """Test parsing valid repository string."""
        client = GitHubClient(token="test_token")
        owner, repo = client._parse_repository("microsoft/vscode")
        assert owner == "microsoft"
        assert repo == "vscode"

    def test_parse_repository_invalid(self):
        """Test parsing invalid repository strings."""
        client = GitHubClient(token="test_token")

        # No slash
        with pytest.raises(ValueError, match="Invalid repository format"):
            client._parse_repository("invalid")

        # Too many parts
        with pytest.raises(ValueError, match="Invalid repository format"):
            client._parse_repository("owner/repo/extra")

        # Empty parts
        with pytest.raises(ValueError, match="Invalid repository format"):
            client._parse_repository("owner/")

    @pytest.mark.asyncio
    async def test_handle_response_success(self):
        """Test handling successful responses."""
        client = GitHubClient(token="test_token")

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"message": "success"}'
        mock_response.json.return_value = {"message": "success"}

        result = await client._handle_response(mock_response)
        assert result == {"message": "success"}

    @pytest.mark.asyncio
    async def test_handle_response_auth_error(self):
        """Test handling authentication errors."""
        client = GitHubClient(token="test_token")

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.content = b'{"message": "Bad credentials"}'
        mock_response.json.return_value = {"message": "Bad credentials"}

        with pytest.raises(GitHubAuthError, match="Authentication failed"):
            await client._handle_response(mock_response)

    @pytest.mark.asyncio
    async def test_handle_response_rate_limit(self):
        """Test handling rate limit errors."""
        client = GitHubClient(token="test_token")

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.content = b'{"message": "API rate limit exceeded"}'
        mock_response.json.return_value = {"message": "API rate limit exceeded"}
        mock_response.headers = {"X-RateLimit-Reset": "1234567890"}

        with pytest.raises(GitHubRateLimitError):
            await client._handle_response(mock_response)

    @pytest.mark.asyncio
    async def test_handle_response_permission_error(self):
        """Test handling permission errors."""
        client = GitHubClient(token="test_token")

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.content = b'{"message": "Forbidden"}'
        mock_response.json.return_value = {"message": "Forbidden"}
        mock_response.headers = {}

        with pytest.raises(GitHubPermissionError):
            await client._handle_response(mock_response)

    @pytest.mark.asyncio
    async def test_handle_response_not_found(self):
        """Test handling repository not found errors."""
        client = GitHubClient(token="test_token")

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.content = b'{"message": "Not Found"}'
        mock_response.json.return_value = {"message": "Not Found"}

        with pytest.raises(GitHubRepositoryNotFoundError):
            await client._handle_response(mock_response)

    @pytest.mark.asyncio
    async def test_handle_response_general_error(self):
        """Test handling general API errors."""
        client = GitHubClient(token="test_token")

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.content = b'{"message": "Internal Server Error"}'
        mock_response.json.return_value = {"message": "Internal Server Error"}

        with pytest.raises(GitHubAPIError):
            await client._handle_response(mock_response)

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_make_request_success(self, mock_client_class):
        """Test making successful API requests."""
        # Setup mock
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"id": 123}'
        mock_response.json.return_value = {"id": 123}
        mock_client.request.return_value = mock_response

        client = GitHubClient(token="test_token")
        result = await client._make_request("GET", "/repos/owner/repo")

        assert result == {"id": 123}
        mock_client.request.assert_called_once()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_make_request_timeout(self, mock_client_class):
        """Test handling request timeouts."""
        # Setup mock to raise timeout
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.request.side_effect = httpx.TimeoutException("Request timeout")

        client = GitHubClient(token="test_token")

        with pytest.raises(GitHubAPIError, match="Request timeout"):
            await client._make_request("GET", "/repos/owner/repo")

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_create_issue_success(self, mock_client_class):
        """Test successful issue creation."""
        # Setup mock
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.content = (
            b'{"number": 123, "html_url": "https://github.com/owner/repo/issues/123"}'
        )
        mock_response.json.return_value = {
            "number": 123,
            "html_url": "https://github.com/owner/repo/issues/123",
            "title": "Test Issue",
            "body": "Test body",
        }
        mock_client.request.return_value = mock_response

        client = GitHubClient(token="test_token")
        result = await client.create_issue(
            repository="owner/repo",
            title="Test Issue",
            body="Test body",
            labels=["bug"],
            assignees=["user1"],
        )

        assert result["number"] == 123
        assert result["html_url"] == "https://github.com/owner/repo/issues/123"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_create_pull_request_success(self, mock_client_class):
        """Test successful pull request creation."""
        # Setup mock
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.content = (
            b'{"number": 456, "html_url": "https://github.com/owner/repo/pull/456"}'
        )
        mock_response.json.return_value = {
            "number": 456,
            "html_url": "https://github.com/owner/repo/pull/456",
            "title": "Test PR",
            "body": "Test PR body",
        }
        mock_client.request.return_value = mock_response

        client = GitHubClient(token="test_token")
        result = await client.create_pull_request(
            repository="owner/repo",
            title="Test PR",
            body="Test PR body",
            head_branch="feature-branch",
            base_branch="main",
        )

        assert result["number"] == 456
        assert result["html_url"] == "https://github.com/owner/repo/pull/456"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_check_repository_permissions_success(self, mock_client_class):
        """Test successful repository permissions check."""
        # Setup mock
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"permissions": {"admin": true, "push": true, "pull": true}, "has_issues": true}'
        mock_response.json.return_value = {
            "permissions": {"admin": True, "push": True, "pull": True},
            "has_issues": True,
        }
        mock_client.request.return_value = mock_response

        client = GitHubClient(token="test_token")
        permissions = await client.check_repository_permissions("owner/repo")

        expected = {
            "read": True,
            "write": True,
            "admin": True,
            "issues": True,
            "pull_requests": True,
        }
        assert permissions == expected
