"""
Tests for API endpoints with Forgejo service support.

LEGACY TEST: This integration test file has been moved to legacy/ to maintain 1:1 correspondence.
Integration tests should be in tests/integration/ directory.
"""

import pytest

# Skip all tests in this legacy file
pytestmark = pytest.mark.skip(
    reason="Legacy integration test - should be moved to tests/integration/"
)

from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from doc_ai_helper_backend.core.exceptions import GitServiceException, NotFoundException
from doc_ai_helper_backend.models.document import (
    DocumentResponse,
    DocumentType,
    DocumentContent,
    DocumentMetadata,
    RepositoryStructureResponse,
    FileTreeItem,
)
from doc_ai_helper_backend.services.git.forgejo_service import ForgejoService


class TestForgejoAPIIntegration:
    """Test cases for API integration with Forgejo service."""

    def setup_method(self):
        """Set up test cases."""
        self.base_url = "https://git.example.com"
        self.access_token = "test_token"
        self.owner = "testowner"
        self.repo = "testrepo"
        self.path = "README.md"
        self.ref = "main"

    @patch("doc_ai_helper_backend.services.git.factory.GitServiceFactory.create")
    @pytest.mark.asyncio
    async def test_get_document_endpoint_with_forgejo(self, mock_create):
        """Test document retrieval endpoint with Forgejo service."""
        # Mock Forgejo service
        mock_service = MagicMock(spec=ForgejoService)
        mock_service.get_document = AsyncMock()

        # Mock document response
        mock_document = DocumentResponse(
            path=self.path,
            name="README.md",
            type=DocumentType.MARKDOWN,
            content=DocumentContent(
                content="# Test\nThis is a test document", encoding="utf-8"
            ),
            metadata=DocumentMetadata(
                size=1024,
                last_modified=datetime.now(),
                content_type="text/markdown",
                sha="abc123",
                download_url=None,
                html_url=None,
                raw_url=None,
                extra={"filename": "README.md", "extension": ".md"},
            ),
            repository=self.repo,
            owner=self.owner,
            service="forgejo",
            ref=self.ref,
            links=[],
        )
        mock_service.get_document.return_value = mock_document
        mock_create.return_value = mock_service

        # Test the service creation and document retrieval
        from doc_ai_helper_backend.services.git.factory import GitServiceFactory

        service = GitServiceFactory.create(
            "forgejo", base_url=self.base_url, access_token=self.access_token
        )
        result = await service.get_document(self.owner, self.repo, self.path, self.ref)

        # Verify the call was made with correct parameters
        mock_create.assert_called_once()
        assert isinstance(result, DocumentResponse)

    @patch("doc_ai_helper_backend.services.git.factory.GitServiceFactory.create")
    @pytest.mark.asyncio
    async def test_get_repository_structure_endpoint_with_forgejo(self, mock_create):
        """Test repository structure endpoint with Forgejo service."""
        # Mock Forgejo service
        mock_service = MagicMock(spec=ForgejoService)
        mock_service.get_repository_structure = AsyncMock()

        from doc_ai_helper_backend.models.document import (
            RepositoryStructureResponse,
            FileTreeItem,
        )

        # Mock repository structure response
        mock_structure = RepositoryStructureResponse(
            service="forgejo",
            owner=self.owner,
            repo=self.repo,
            ref=self.ref,
            tree=[
                FileTreeItem(
                    name="README.md",
                    path="README.md",
                    type="file",
                    size=1024,
                    sha="abc123",
                    download_url=None,
                    html_url=None,
                    git_url=None,
                )
            ],
            last_updated=datetime.now(),
        )
        mock_service.get_repository_structure.return_value = mock_structure
        mock_create.return_value = mock_service

        # Test the service creation and structure retrieval
        from doc_ai_helper_backend.services.git.factory import GitServiceFactory

        service = GitServiceFactory.create(
            "forgejo", base_url=self.base_url, access_token=self.access_token
        )
        result = await service.get_repository_structure(self.owner, self.repo, self.ref)

        # Verify the call was made with correct parameters
        mock_create.assert_called_once()
        assert isinstance(result, RepositoryStructureResponse)
        assert result.service == "forgejo"

    @pytest.mark.asyncio
    async def test_forgejo_service_authentication_methods(self):
        """Test Forgejo service authentication methods."""
        # Test token authentication
        service_token = ForgejoService(
            base_url=self.base_url, access_token=self.access_token
        )
        auth_headers_token = service_token._get_auth_headers()
        assert "Authorization" in auth_headers_token
        assert auth_headers_token["Authorization"] == f"Bearer {self.access_token}"

        # Test basic authentication
        username = "testuser"
        password = "testpass"
        service_basic = ForgejoService(
            base_url=self.base_url, username=username, password=password
        )
        auth_headers_basic = service_basic._get_auth_headers()
        assert "Authorization" in auth_headers_basic
        assert auth_headers_basic["Authorization"].startswith("Basic ")

    def test_forgejo_service_configuration(self):
        """Test Forgejo service configuration."""
        service = ForgejoService(base_url=self.base_url, access_token=self.access_token)

        assert service.base_url == self.base_url
        assert service.api_base_url == f"{self.base_url}/api/v1"
        assert service.access_token == self.access_token
        assert service._get_service_name() == "forgejo"

        # Test supported authentication methods
        auth_methods = service.get_supported_auth_methods()
        assert "token" in auth_methods
        assert "basic_auth" in auth_methods

    @pytest.mark.asyncio
    async def test_forgejo_error_handling(self):
        """Test error handling in Forgejo service."""
        service = ForgejoService(base_url=self.base_url, access_token=self.access_token)

        # Test repository not found error
        service.check_repository_exists = AsyncMock(return_value=False)

        with pytest.raises(NotFoundException) as exc_info:
            await service.get_document(self.owner, "nonexistent", self.path)

        assert "Repository testowner/nonexistent not found" in str(exc_info.value)

    def test_forgejo_url_normalization(self):
        """Test URL normalization in Forgejo service."""
        # Test with trailing slash
        service_with_slash = ForgejoService(base_url="https://git.example.com/")
        assert service_with_slash.base_url == "https://git.example.com"
        assert service_with_slash.api_base_url == "https://git.example.com/api/v1"

        # Test without trailing slash
        service_without_slash = ForgejoService(base_url="https://git.example.com")
        assert service_without_slash.base_url == "https://git.example.com"
        assert service_without_slash.api_base_url == "https://git.example.com/api/v1"

    @patch("doc_ai_helper_backend.services.git.factory.settings")
    def test_forgejo_factory_integration(self, mock_settings):
        """Test Forgejo service creation through factory."""
        mock_settings.forgejo_base_url = self.base_url
        mock_settings.forgejo_token = self.access_token
        mock_settings.forgejo_username = None
        mock_settings.forgejo_password = None

        from doc_ai_helper_backend.services.git.factory import GitServiceFactory

        service = GitServiceFactory.create("forgejo", base_url=self.base_url)
        assert isinstance(service, ForgejoService)
        assert service.base_url == self.base_url
        assert service.access_token == self.access_token
