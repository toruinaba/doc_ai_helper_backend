"""
Mock service for testing.
"""

from unittest.mock import MagicMock, AsyncMock

# Create mock objects for services
mock_document_service = AsyncMock()
mock_repository_service = AsyncMock()
mock_search_service = AsyncMock()

# Mock the endpoints module to use these mocks
from doc_ai_helper_backend.api.endpoints import documents, repositories, search

# Patch the document service
documents.get_document = mock_document_service.get_document
documents.get_repository_structure = mock_document_service.get_repository_structure

# Patch the repository service
repositories.list_repositories = mock_repository_service.list_repositories
repositories.create_repository = mock_repository_service.create_repository
repositories.get_repository = mock_repository_service.get_repository
repositories.update_repository = mock_repository_service.update_repository
repositories.delete_repository = mock_repository_service.delete_repository

# Patch the search service
search.search_repository = mock_search_service.search_repository
