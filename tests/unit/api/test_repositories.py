"""
Unit tests for Repository API endpoints.

Tests CRUD operations, feature flags, error handling, and 
delegation pattern for repository management API.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from doc_ai_helper_backend.main import app
from doc_ai_helper_backend.models.repository import (
    GitServiceType,
    RepositoryCreate,
    RepositoryResponse,
    RepositoryUpdate,
)
from doc_ai_helper_backend.models.repository_context import RepositoryContext, GitService
from doc_ai_helper_backend.core.exceptions import RepositoryServiceException


@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)


@pytest.fixture
def sample_repository_response():
    """Sample repository response."""
    return RepositoryResponse(
        id=1,
        name="test-repo",
        owner="test-owner",
        service_type=GitServiceType.GITHUB,
        url="https://github.com/test-owner/test-repo",
        base_url=None,
        default_branch="main",
        root_path="docs",
        description="Test repository",
        is_public=True,
        supported_branches=["main", "develop"],
        metadata={"project_type": "documentation"},
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
    )


@pytest.fixture
def sample_repository_create():
    """Sample repository creation data."""
    return {
        "name": "test-repo",
        "owner": "test-owner",
        "service_type": "github",
        "url": "https://github.com/test-owner/test-repo",
        "default_branch": "main",
        "root_path": "docs",
        "description": "Test repository",
        "is_public": True,
        "access_token": "test-token",
        "metadata": {"project_type": "documentation"},
    }


class TestRepositoryListEndpoint:
    """Test repository list endpoint."""

    @patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True)
    @patch("doc_ai_helper_backend.api.dependencies.get_repository_service")
    def test_list_repositories_success(self, mock_get_service, client, sample_repository_response):
        """Test successful repository listing."""
        # Mock service
        mock_service = AsyncMock()
        mock_service.list_repositories.return_value = [sample_repository_response]
        mock_get_service.return_value = mock_service

        # Execute
        response = client.get("/api/v1/repositories/")

        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "test-repo"
        assert data[0]["owner"] == "test-owner"

    @patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", False)
    def test_list_repositories_feature_disabled(self, client):
        """Test repository listing with feature disabled."""
        # Execute
        response = client.get("/api/v1/repositories/")

        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not enabled" in response.json()["detail"]

    @patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True)
    @patch("doc_ai_helper_backend.api.dependencies.get_repository_service")
    def test_list_repositories_pagination_validation(self, mock_get_service, client):
        """Test repository listing with invalid pagination parameters."""
        # Mock service
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        # Test negative skip
        response = client.get("/api/v1/repositories/?skip=-1")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Test invalid limit
        response = client.get("/api/v1/repositories/?limit=0")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response = client.get("/api/v1/repositories/?limit=2000")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True)
    @patch("doc_ai_helper_backend.api.dependencies.get_repository_service")
    def test_list_repositories_service_error(self, mock_get_service, client):
        """Test repository listing with service error."""
        # Mock service error
        mock_service = AsyncMock()
        mock_service.list_repositories.side_effect = RepositoryServiceException("Database error")
        mock_get_service.return_value = mock_service

        # Execute
        response = client.get("/api/v1/repositories/")

        # Verify
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestRepositoryCreateEndpoint:
    """Test repository create endpoint."""

    @patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True)
    @patch("doc_ai_helper_backend.api.dependencies.get_repository_service")
    def test_create_repository_success(
        self, mock_get_service, client, sample_repository_create, sample_repository_response
    ):
        """Test successful repository creation."""
        # Mock service
        mock_service = AsyncMock()
        mock_service.create_repository.return_value = sample_repository_response
        mock_get_service.return_value = mock_service

        # Execute
        response = client.post("/api/v1/repositories/", json=sample_repository_create)

        # Verify
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "test-repo"
        assert data["id"] == 1

    @patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", False)
    def test_create_repository_feature_disabled(self, client, sample_repository_create):
        """Test repository creation with feature disabled."""
        # Execute
        response = client.post("/api/v1/repositories/", json=sample_repository_create)

        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True)
    @patch("doc_ai_helper_backend.api.dependencies.get_repository_service")
    def test_create_repository_duplicate_error(self, mock_get_service, client, sample_repository_create):
        """Test repository creation with duplicate error."""
        # Mock service duplicate error
        mock_service = AsyncMock()
        mock_service.create_repository.side_effect = RepositoryServiceException(
            "Repository already exists: github/test-owner/test-repo"
        )
        mock_get_service.return_value = mock_service

        # Execute
        response = client.post("/api/v1/repositories/", json=sample_repository_create)

        # Verify
        assert response.status_code == status.HTTP_409_CONFLICT


class TestRepositoryGetEndpoint:
    """Test repository get endpoint."""

    @patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True)
    @patch("doc_ai_helper_backend.api.dependencies.get_repository_service")
    def test_get_repository_success(self, mock_get_service, client, sample_repository_response):
        """Test successful repository retrieval."""
        # Mock service
        mock_service = AsyncMock()
        mock_service.get_repository.return_value = sample_repository_response
        mock_get_service.return_value = mock_service

        # Execute
        response = client.get("/api/v1/repositories/1")

        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "test-repo"

    @patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True)
    @patch("doc_ai_helper_backend.api.dependencies.get_repository_service")
    def test_get_repository_not_found(self, mock_get_service, client):
        """Test repository retrieval when not found."""
        # Mock service returning None
        mock_service = AsyncMock()
        mock_service.get_repository.return_value = None
        mock_get_service.return_value = mock_service

        # Execute
        response = client.get("/api/v1/repositories/999")

        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True)
    def test_get_repository_invalid_id(self, client):
        """Test repository retrieval with invalid ID."""
        # Execute with invalid ID
        response = client.get("/api/v1/repositories/0")

        # Verify
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Execute with negative ID
        response = client.get("/api/v1/repositories/-1")

        # Verify
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestRepositoryUpdateEndpoint:
    """Test repository update endpoint."""

    @patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True)
    @patch("doc_ai_helper_backend.api.dependencies.get_repository_service")
    def test_update_repository_success(self, mock_get_service, client, sample_repository_response):
        """Test successful repository update."""
        # Mock service
        mock_service = AsyncMock()
        mock_service.update_repository.return_value = sample_repository_response
        mock_get_service.return_value = mock_service

        # Update data
        update_data = {"description": "Updated description"}

        # Execute
        response = client.put("/api/v1/repositories/1", json=update_data)

        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == 1

    @patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True)
    @patch("doc_ai_helper_backend.api.dependencies.get_repository_service")
    def test_update_repository_not_found(self, mock_get_service, client):
        """Test repository update when not found."""
        # Mock service returning None
        mock_service = AsyncMock()
        mock_service.update_repository.return_value = None
        mock_get_service.return_value = mock_service

        # Update data
        update_data = {"description": "Updated description"}

        # Execute
        response = client.put("/api/v1/repositories/999", json=update_data)

        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRepositoryDeleteEndpoint:
    """Test repository delete endpoint."""

    @patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True)
    @patch("doc_ai_helper_backend.api.dependencies.get_repository_service")
    def test_delete_repository_success(self, mock_get_service, client):
        """Test successful repository deletion."""
        # Mock service
        mock_service = AsyncMock()
        mock_service.delete_repository.return_value = True
        mock_get_service.return_value = mock_service

        # Execute
        response = client.delete("/api/v1/repositories/1")

        # Verify
        assert response.status_code == status.HTTP_204_NO_CONTENT

    @patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True)
    @patch("doc_ai_helper_backend.api.dependencies.get_repository_service")
    def test_delete_repository_not_found(self, mock_get_service, client):
        """Test repository deletion when not found."""
        # Mock service returning False
        mock_service = AsyncMock()
        mock_service.delete_repository.return_value = False
        mock_get_service.return_value = mock_service

        # Execute
        response = client.delete("/api/v1/repositories/999")

        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRepositoryContextEndpoint:
    """Test repository context generation endpoint."""

    @patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True)
    @patch("doc_ai_helper_backend.api.dependencies.get_repository_service")
    def test_get_repository_context_success(self, mock_get_service, client, sample_repository_response):
        """Test successful repository context generation."""
        # Mock service
        mock_service = AsyncMock()
        mock_service.get_repository.return_value = sample_repository_response
        mock_get_service.return_value = mock_service

        # Execute
        response = client.get("/api/v1/repositories/1/context?ref=feature/test&current_path=docs/api.md")

        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["service"] == "github"
        assert data["owner"] == "test-owner"
        assert data["repo"] == "test-repo"
        assert data["ref"] == "feature/test"
        assert data["current_path"] == "docs/api.md"

    @patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True)
    @patch("doc_ai_helper_backend.api.dependencies.get_repository_service")
    def test_get_repository_context_defaults(self, mock_get_service, client, sample_repository_response):
        """Test repository context generation with default values."""
        # Mock service
        mock_service = AsyncMock()
        mock_service.get_repository.return_value = sample_repository_response
        mock_get_service.return_value = mock_service

        # Execute without parameters
        response = client.get("/api/v1/repositories/1/context")

        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["ref"] == "main"  # default_branch
        assert data["current_path"] is None

    @patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True)
    @patch("doc_ai_helper_backend.api.dependencies.get_repository_service")
    def test_get_repository_context_not_found(self, mock_get_service, client):
        """Test repository context generation when repository not found."""
        # Mock service returning None
        mock_service = AsyncMock()
        mock_service.get_repository.return_value = None
        mock_get_service.return_value = mock_service

        # Execute
        response = client.get("/api/v1/repositories/999/context")

        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRepositoryAPIIntegration:
    """Test integrated API functionality."""

    @patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True)
    @patch("doc_ai_helper_backend.api.dependencies.get_repository_service")
    def test_repository_crud_workflow(
        self, 
        mock_get_service, 
        client, 
        sample_repository_create, 
        sample_repository_response
    ):
        """Test complete CRUD workflow."""
        # Mock service
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        # Create
        mock_service.create_repository.return_value = sample_repository_response
        create_response = client.post("/api/v1/repositories/", json=sample_repository_create)
        assert create_response.status_code == status.HTTP_201_CREATED

        # Read
        mock_service.get_repository.return_value = sample_repository_response
        get_response = client.get("/api/v1/repositories/1")
        assert get_response.status_code == status.HTTP_200_OK

        # Update
        mock_service.update_repository.return_value = sample_repository_response
        update_response = client.put("/api/v1/repositories/1", json={"description": "Updated"})
        assert update_response.status_code == status.HTTP_200_OK

        # Delete
        mock_service.delete_repository.return_value = True
        delete_response = client.delete("/api/v1/repositories/1")
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    @patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True)
    @patch("doc_ai_helper_backend.api.dependencies.get_repository_service")
    def test_delegation_pattern_integration(
        self, mock_get_service, client, sample_repository_response
    ):
        """Test delegation pattern in API workflow."""
        # Mock service
        mock_service = AsyncMock()
        mock_service.get_repository.return_value = sample_repository_response
        mock_get_service.return_value = mock_service

        # Get repository (delegation pattern available)
        repo_response = client.get("/api/v1/repositories/1")
        assert repo_response.status_code == status.HTTP_200_OK
        
        # Generate context (delegation pattern in action)
        context_response = client.get("/api/v1/repositories/1/context?current_path=docs/guide.md")
        assert context_response.status_code == status.HTTP_200_OK
        
        context_data = context_response.json()
        assert context_data["current_path"] == "docs/guide.md"
        
        # Verify the repository data can be used for LLM integration
        assert "service" in context_data
        assert "owner" in context_data
        assert "repo" in context_data