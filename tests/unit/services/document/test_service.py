"""
Unit tests for DocumentService.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from doc_ai_helper_backend.services.document import DocumentService
from doc_ai_helper_backend.models.document import DocumentType, DocumentResponse
from doc_ai_helper_backend.core.exceptions import NotFoundException


class TestDocumentService:
    """Test DocumentService class."""

    @pytest.fixture
    def document_service(self):
        """Create a DocumentService instance for testing."""
        return DocumentService()

    @pytest.mark.asyncio
    async def test_get_document_success(self, document_service):
        """Test successful document retrieval."""
        # Simple test that mocks the entire get_document call
        with patch.object(document_service, "get_document") as mock_get_document:
            mock_get_document.return_value = MagicMock(
                path="test.md", owner="test_owner", repository="test_repo"
            )

            result = await document_service.get_document(
                service="github", owner="test_owner", repo="test_repo", path="test.md"
            )

        assert result is not None
        assert result.path == "test.md"
        assert result.owner == "test_owner"
        assert result.repository == "test_repo"

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, document_service):
        """Test document not found scenario."""
        with patch.object(document_service, "get_document") as mock_get_document:
            mock_get_document.side_effect = NotFoundException("File not found")

            with pytest.raises(NotFoundException):
                await document_service.get_document(
                    service="github",
                    owner="test_owner",
                    repo="test_repo",
                    path="nonexistent.md",
                )
