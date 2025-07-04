"""
Tests for Forgejo service implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from doc_ai_helper_backend.core.exceptions import (
    GitServiceException,
    NotFoundException,
    UnauthorizedException,
)
from doc_ai_helper_backend.services.git.forgejo_service import ForgejoService


class TestForgejoService:
    """Test cases for ForgejoService."""

    def setup_method(self):
        """Set up test cases."""
        self.base_url = "https://git.example.com"
        self.access_token = "test_token"
        self.username = "testuser"
        self.password = "testpass"

    def test_init_with_token(self):
        """Test initialization with access token."""
        service = ForgejoService(base_url=self.base_url, access_token=self.access_token)

        assert service.base_url == self.base_url
        assert service.api_base_url == f"{self.base_url}/api/v1"
        assert service.access_token == self.access_token
        assert service._get_service_name() == "forgejo"

    def test_init_with_basic_auth(self):
        """Test initialization with basic authentication."""
        service = ForgejoService(
            base_url=self.base_url, username=self.username, password=self.password
        )

        assert service.username == self.username
        assert service.password == self.password
        assert service.access_token is None

    def test_init_without_auth(self):
        """Test initialization without authentication."""
        # Should not raise exception, just log warning
        service = ForgejoService(base_url=self.base_url)
        assert service.access_token is None
        assert service.username is None
        assert service.password is None

    def test_get_supported_auth_methods(self):
        """Test getting supported authentication methods."""
        service = ForgejoService(base_url=self.base_url)
        auth_methods = service.get_supported_auth_methods()
        assert "token" in auth_methods
        assert "basic_auth" in auth_methods

    def test_get_auth_headers_with_token(self):
        """Test getting auth headers with token."""
        service = ForgejoService(base_url=self.base_url, access_token=self.access_token)
        headers = service._get_auth_headers()
        assert headers["Authorization"] == f"Bearer {self.access_token}"

    def test_get_auth_headers_with_basic_auth(self):
        """Test getting auth headers with basic auth."""
        service = ForgejoService(
            base_url=self.base_url, username=self.username, password=self.password
        )
        headers = service._get_auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")

    @pytest.mark.asyncio
    async def test_authenticate_success(self):
        """Test successful authentication."""
        service = ForgejoService(base_url=self.base_url, access_token=self.access_token)

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            service._make_request = AsyncMock(return_value=mock_response)

            result = await service.authenticate()
            assert result is True

    @pytest.mark.asyncio
    async def test_authenticate_failure(self):
        """Test authentication failure."""
        service = ForgejoService(base_url=self.base_url, access_token="invalid_token")

        with patch("httpx.AsyncClient") as mock_client:
            service._make_request = AsyncMock(
                side_effect=UnauthorizedException("Unauthorized")
            )

            result = await service.authenticate()
            assert result is False

    @pytest.mark.asyncio
    async def test_check_repository_exists_true(self):
        """Test repository exists check - exists."""
        service = ForgejoService(base_url=self.base_url, access_token=self.access_token)

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await service.check_repository_exists("owner", "repo")
            assert result is True

    @pytest.mark.asyncio
    async def test_check_repository_exists_false(self):
        """Test repository exists check - not exists."""
        service = ForgejoService(base_url=self.base_url, access_token=self.access_token)

        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await service.check_repository_exists("owner", "repo")
            assert result is False

    @pytest.mark.asyncio
    async def test_get_document_not_found_repo(self):
        """Test get document with non-existent repository."""
        service = ForgejoService(base_url=self.base_url, access_token=self.access_token)

        service.check_repository_exists = AsyncMock(return_value=False)

        with pytest.raises(NotFoundException):
            await service.get_document("owner", "repo", "README.md")

    def test_base_url_stripping(self):
        """Test that trailing slashes are stripped from base URL."""
        service = ForgejoService(base_url="https://git.example.com/")
        assert service.base_url == "https://git.example.com"
        assert service.api_base_url == "https://git.example.com/api/v1"
