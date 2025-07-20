"""
Unit tests for Repository API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime

from doc_ai_helper_backend.main import app
from doc_ai_helper_backend.models.repository import (
    GitServiceType,
    RepositoryCreate,
    RepositoryResponse,
    RepositoryUpdate,
)
from doc_ai_helper_backend.models.repository_context import RepositoryContext, GitService
from doc_ai_helper_backend.core.exceptions import RepositoryServiceException
from doc_ai_helper_backend.api.dependencies import get_repository_service


class TestRepositoryAPI:
    """Unit tests for Repository API endpoints."""

    @pytest.fixture
    def client(self):
        """Test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_repository_response(self):
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
            created_at=datetime(2025, 1, 1),
            updated_at=datetime(2025, 1, 1),
        )

    @pytest.mark.asyncio
    async def test_feature_flag_disabled(self, client):
        """Test repository endpoints when feature flag is disabled."""
        with patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", False):
            response = client.get("/api/v1/repositories/")
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Repository management feature is not enabled" in response.json()["detail"]

    @pytest.mark.asyncio 
    async def test_list_repositories_success(self, client, sample_repository_response):
        """Test successful repository listing."""
        with patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True):
            mock_service = AsyncMock()
            mock_service.list_repositories.return_value = [sample_repository_response]
            
            app.dependency_overrides[get_repository_service] = lambda: mock_service
            
            try:
                response = client.get("/api/v1/repositories/")
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert len(data) == 1
                assert data[0]["name"] == "test-repo"
                assert data[0]["owner"] == "test-owner"
            finally:
                app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_repositories_empty(self, client):
        """Test repository listing with no results."""
        with patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True):
            mock_service = AsyncMock()
            mock_service.list_repositories.return_value = []
            
            app.dependency_overrides[get_repository_service] = lambda: mock_service
            
            try:
                response = client.get("/api/v1/repositories/")
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert len(data) == 0
            finally:
                app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_repository_success(self, client, sample_repository_response):
        """Test successful repository creation."""
        with patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True):
            mock_service = AsyncMock()
            mock_service.create_repository.return_value = sample_repository_response
            
            app.dependency_overrides[get_repository_service] = lambda: mock_service
            
            try:
                repository_data = {
                    "name": "test-repo",
                    "owner": "test-owner",
                    "service_type": "github",
                    "url": "https://github.com/test-owner/test-repo",
                    "description": "Test repository"
                }

                response = client.post("/api/v1/repositories/", json=repository_data)
                
                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["name"] == "test-repo"
                assert data["owner"] == "test-owner"
            finally:
                app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_repository_validation_error(self, client):
        """Test repository creation with validation error."""
        with patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True):
            invalid_data = {
                "name": "",  # Invalid empty name
                "owner": "test-owner",
                "service_type": "invalid_service",  # Invalid service type
                "url": "not-a-url"  # Invalid URL
            }

            response = client.post("/api/v1/repositories/", json=invalid_data)
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_get_repository_success(self, client, sample_repository_response):
        """Test successful repository retrieval."""
        with patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True):
            mock_service = AsyncMock()
            mock_service.get_repository.return_value = sample_repository_response
            
            app.dependency_overrides[get_repository_service] = lambda: mock_service
            
            try:
                response = client.get("/api/v1/repositories/1")
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["id"] == 1
                assert data["name"] == "test-repo"
            finally:
                app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_repository_not_found(self, client):
        """Test repository retrieval when not found."""
        with patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True):
            mock_service = AsyncMock()
            mock_service.get_repository.return_value = None
            
            app.dependency_overrides[get_repository_service] = lambda: mock_service
            
            try:
                response = client.get("/api/v1/repositories/999")
                
                assert response.status_code == status.HTTP_404_NOT_FOUND
            finally:
                app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_repository_success(self, client, sample_repository_response):
        """Test successful repository update."""
        with patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True):
            # Create updated response
            updated_response = sample_repository_response.model_copy()
            updated_response.description = "Updated description"
            
            mock_service = AsyncMock()
            mock_service.update_repository.return_value = updated_response
            
            app.dependency_overrides[get_repository_service] = lambda: mock_service
            
            try:
                update_data = {"description": "Updated description"}
                response = client.put("/api/v1/repositories/1", json=update_data)
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["description"] == "Updated description"
            finally:
                app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_repository_success(self, client):
        """Test successful repository deletion."""
        with patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True):
            mock_service = AsyncMock()
            mock_service.delete_repository.return_value = True
            
            app.dependency_overrides[get_repository_service] = lambda: mock_service
            
            try:
                response = client.delete("/api/v1/repositories/1")
                
                assert response.status_code == status.HTTP_204_NO_CONTENT
            finally:
                app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_repository_context_success(self, client, sample_repository_response):
        """Test successful repository context retrieval."""
        with patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True):
            mock_service = AsyncMock()
            mock_service.get_repository.return_value = sample_repository_response
            
            app.dependency_overrides[get_repository_service] = lambda: mock_service
            
            try:
                response = client.get("/api/v1/repositories/1/context?ref=feature/test&current_path=docs/api.md")
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["service"] == "github"
                assert data["owner"] == "test-owner"
                assert data["repo"] == "test-repo"
                assert data["ref"] == "feature/test"
                assert data["current_path"] == "docs/api.md"
            finally:
                app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_repository_context_defaults(self, client, sample_repository_response):
        """Test repository context retrieval with default values."""
        with patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True):
            mock_service = AsyncMock()
            mock_service.get_repository.return_value = sample_repository_response
            
            app.dependency_overrides[get_repository_service] = lambda: mock_service
            
            try:
                response = client.get("/api/v1/repositories/1/context")
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["service"] == "github"
                assert data["owner"] == "test-owner"
                assert data["repo"] == "test-repo"
                assert data["ref"] == "main"  # default branch
                assert data["current_path"] is None
            finally:
                app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_service_error_handling(self, client):
        """Test API error handling when service raises exception."""
        with patch("doc_ai_helper_backend.core.config.settings.enable_repository_management", True):
            mock_service = AsyncMock()
            mock_service.list_repositories.side_effect = RepositoryServiceException("Service error")
            
            app.dependency_overrides[get_repository_service] = lambda: mock_service
            
            try:
                response = client.get("/api/v1/repositories/")
                
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            finally:
                app.dependency_overrides.clear()