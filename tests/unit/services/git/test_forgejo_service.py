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

    @pytest.mark.asyncio
    async def test_create_issue(self):
        """Test issue creation."""
        service = ForgejoService(base_url=self.base_url, access_token=self.access_token)

        # モックレスポンス
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 123,
            "number": 123,
            "title": "Test Issue",
            "body": "Test description",
            "state": "open",
            "html_url": f"{self.base_url}/owner/repo/issues/123",
        }

        with patch.object(
            service, "_make_request", new_callable=AsyncMock
        ) as mock_make_request, patch.object(
            service, "_resolve_label_names_to_ids", new_callable=AsyncMock
        ) as mock_resolve_labels:
            mock_make_request.return_value = mock_response
            mock_resolve_labels.return_value = [1]  # Mock label ID resolution

            result = await service.create_issue(
                "owner", "repo", "Test Issue", "Test description", labels=["bug"]
            )

            assert result["id"] == 123
            assert result["title"] == "Test Issue"
            # Verify that label resolution was called
            mock_resolve_labels.assert_called_once_with("owner", "repo", ["bug"])

    @pytest.mark.asyncio
    async def test_create_issue_without_labels(self):
        """Test issue creation without labels."""
        service = ForgejoService(base_url=self.base_url, access_token=self.access_token)

        # モックレスポンス
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 124,
            "number": 124,
            "title": "Test Issue No Labels",
            "body": "Test description",
            "state": "open",
            "html_url": f"{self.base_url}/owner/repo/issues/124",
        }

        with patch.object(
            service, "_make_request", new_callable=AsyncMock
        ) as mock_make_request:
            mock_make_request.return_value = mock_response

            result = await service.create_issue(
                "owner", "repo", "Test Issue No Labels", "Test description"
            )

            assert result["id"] == 124
            assert result["title"] == "Test Issue No Labels"

    @pytest.mark.asyncio
    async def test_get_repository_labels(self):
        """Test getting repository labels."""
        service = ForgejoService(base_url=self.base_url, access_token=self.access_token)

        # モックレスポンス
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": 1, "name": "bug", "color": "d73a4a"},
            {"id": 2, "name": "enhancement", "color": "a2eeef"},
            {"id": 3, "name": "documentation", "color": "0075ca"},
        ]

        with patch.object(
            service, "_make_request", new_callable=AsyncMock
        ) as mock_make_request:
            mock_make_request.return_value = mock_response

            result = await service.get_repository_labels("owner", "repo")

            assert len(result) == 3
            assert result[0]["name"] == "bug"
            assert result[0]["id"] == 1
            assert result[1]["name"] == "enhancement"
            assert result[1]["id"] == 2

    @pytest.mark.asyncio
    async def test_resolve_label_names_to_ids(self):
        """Test resolving label names to IDs."""
        service = ForgejoService(base_url=self.base_url, access_token=self.access_token)

        # Mock repository labels
        mock_labels = [
            {"id": 1, "name": "bug", "color": "d73a4a"},
            {"id": 2, "name": "enhancement", "color": "a2eeef"},
            {"id": 3, "name": "documentation", "color": "0075ca"},
        ]

        with patch.object(
            service, "get_repository_labels", new_callable=AsyncMock
        ) as mock_get_labels:
            mock_get_labels.return_value = mock_labels

            # Test resolving existing labels
            result = await service._resolve_label_names_to_ids(
                "owner", "repo", ["bug", "enhancement"]
            )
            assert result == [1, 2]

            # Test with some non-existent labels
            result = await service._resolve_label_names_to_ids(
                "owner", "repo", ["bug", "nonexistent", "documentation"]
            )
            assert result == [1, 3]  # Should skip non-existent labels

            # Test with empty labels
            result = await service._resolve_label_names_to_ids("owner", "repo", [])
            assert result == []

    @pytest.mark.asyncio
    async def test_create_pull_request(self):
        """Test pull request creation."""
        service = ForgejoService(base_url=self.base_url, access_token=self.access_token)

        # モックレスポンス
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 456,
            "number": 456,
            "title": "Test PR",
            "body": "Test PR description",
            "state": "open",
            "draft": False,
            "html_url": f"{self.base_url}/owner/repo/pulls/456",
            "head": {"ref": "feature-branch"},
            "base": {"ref": "main"},
        }

        with patch.object(
            service, "_make_request", new_callable=AsyncMock
        ) as mock_make_request:
            mock_make_request.return_value = mock_response

            result = await service.create_pull_request(
                "owner",
                "repo",
                "Test PR",
                "Test PR description",
                "feature-branch",
                "main",
            )

            assert result["id"] == 456
            assert result["title"] == "Test PR"
            assert result["draft"] is False

    @pytest.mark.asyncio
    async def test_create_pull_request_draft(self):
        """Test draft pull request creation."""
        service = ForgejoService(base_url=self.base_url, access_token=self.access_token)

        # モックレスポンス
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 789,
            "number": 789,
            "title": "Draft PR",
            "body": "Draft PR description",
            "state": "open",
            "draft": True,
            "html_url": f"{self.base_url}/owner/repo/pulls/789",
            "head": {"ref": "draft-branch"},
            "base": {"ref": "main"},
        }

        with patch.object(
            service, "_make_request", new_callable=AsyncMock
        ) as mock_make_request:
            mock_make_request.return_value = mock_response

            result = await service.create_pull_request(
                "owner",
                "repo",
                "Draft PR",
                "Draft PR description",
                "draft-branch",
                "main",
                draft=True,
            )

            assert result["id"] == 789
            assert result["title"] == "Draft PR"
            assert result["draft"] is True

    @pytest.mark.asyncio
    async def test_check_repository_permissions(self):
        """Test repository permissions check."""
        service = ForgejoService(base_url=self.base_url, access_token=self.access_token)

        # モックレスポンス
        mock_repo_info = {
            "permissions": {"pull": True, "push": True, "admin": False},
            "has_issues": True,
        }

        with patch.object(
            service, "get_repository_info", new_callable=AsyncMock
        ) as mock_get_repo_info:
            mock_get_repo_info.return_value = mock_repo_info

            result = await service.check_repository_permissions("owner", "repo")

            assert result["read"] is True
            assert result["write"] is True
            assert result["admin"] is False
            assert result["issues"] is True

    @pytest.mark.asyncio
    async def test_get_repository_info(self):
        """Test repository info retrieval."""
        service = ForgejoService(base_url=self.base_url, access_token=self.access_token)

        # モックレスポンス
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 12345,
            "name": "test-repo",
            "full_name": "owner/test-repo",
            "owner": {"login": "owner"},
            "description": "Test repository",
            "private": False,
            "html_url": f"{self.base_url}/owner/test-repo",
            "clone_url": f"{self.base_url}/owner/test-repo.git",
            "default_branch": "main",
        }

        with patch.object(
            service, "_make_request", new_callable=AsyncMock
        ) as mock_make_request:
            mock_make_request.return_value = mock_response

            result = await service.get_repository_info("owner", "test-repo")

            assert result["id"] == 12345
            assert result["name"] == "test-repo"
            assert result["full_name"] == "owner/test-repo"
