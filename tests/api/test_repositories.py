"""
Test repository-related endpoints.
"""

import pytest
from datetime import datetime
from unittest.mock import patch

from doc_ai_helper_backend.core.config import settings
from doc_ai_helper_backend.core.exceptions import NotFoundException
from doc_ai_helper_backend.models.repository import GitServiceType
from tests.api.mock_services import mock_repository_service


@pytest.fixture
def mock_repository_data():
    """Create mock repository data."""
    return {
        "id": 1,
        "name": "test-repo",
        "owner": "test-owner",
        "service_type": GitServiceType.GITHUB,
        "url": "https://github.com/test-owner/test-repo",
        "branch": "main",
        "description": "Test repository",
        "is_public": True,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "metadata": {"stars": 10, "forks": 5},
    }


@patch("doc_ai_helper_backend.api.endpoints.repositories.list_repositories")
def test_list_repositories(mock_list_repos, client, mock_repository_data):
    """Test list repositories endpoint."""
    # Setup mock
    mock_list_repos.return_value = [mock_repository_data]

    # Test
    response = client.get(f"{settings.api_prefix}/repositories/")

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "test-repo"
    assert data[0]["owner"] == "test-owner"

    # Verify mock was called with correct parameters
    mock_list_repos.assert_called_once_with(skip=0, limit=100)


@patch("doc_ai_helper_backend.api.endpoints.repositories.create_repository")
def test_create_repository(mock_create_repo, client, mock_repository_data):
    """Test create repository endpoint."""
    # Setup mock
    mock_create_repo.return_value = mock_repository_data

    # Create repository data for request
    repo_data = {
        "name": "new-repo",
        "owner": "test-owner",
        "service_type": "github",
        "url": "https://github.com/test-owner/new-repo",
        "branch": "main",
        "description": "New test repository",
        "is_public": True,
        "access_token": "test-token",
        "metadata": {"stars": 0, "forks": 0},
    }

    # Test
    response = client.post(f"{settings.api_prefix}/repositories/", json=repo_data)

    # Verify
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-repo"  # From mock data
    assert data["owner"] == "test-owner"
    assert "id" in data

    # Verify mock was called
    mock_create_repo.assert_called_once()


@patch("doc_ai_helper_backend.api.endpoints.repositories.get_repository")
def test_get_repository(mock_get_repo, client, mock_repository_data):
    """Test get repository endpoint."""
    # Setup mock
    mock_get_repo.return_value = mock_repository_data

    # Test
    response = client.get(f"{settings.api_prefix}/repositories/1")

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "test-repo"
    assert data["owner"] == "test-owner"

    # Verify mock was called with correct parameters
    mock_get_repo.assert_called_once_with(repository_id=1)


@patch("doc_ai_helper_backend.api.endpoints.repositories.get_repository")
def test_get_repository_not_found(mock_get_repo, client):
    """Test get repository endpoint with not found error."""
    # Setup mock to raise exception
    mock_get_repo.side_effect = NotFoundException("Repository not found")

    # Test
    response = client.get(f"{settings.api_prefix}/repositories/999")

    # Verify
    assert response.status_code == 404
    assert "message" in response.json()
    assert response.json()["message"] == "Repository not found"


@patch("doc_ai_helper_backend.api.endpoints.repositories.update_repository")
def test_update_repository(mock_update_repo, client, mock_repository_data):
    """Test update repository endpoint."""
    # Setup mock
    mock_update_repo.return_value = mock_repository_data

    # Update data
    update_data = {"description": "Updated description", "branch": "develop"}

    # Test
    response = client.put(f"{settings.api_prefix}/repositories/1", json=update_data)

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "test-repo"

    # Verify mock was called with correct parameters
    mock_update_repo.assert_called_once()


@patch("doc_ai_helper_backend.api.endpoints.repositories.delete_repository")
def test_delete_repository(mock_delete_repo, client):
    """Test delete repository endpoint."""
    # Setup mock
    mock_delete_repo.return_value = None

    # Test
    response = client.delete(f"{settings.api_prefix}/repositories/1")

    # Verify
    assert response.status_code == 204
    assert response.content == b""  # No content in response

    # Verify mock was called with correct parameters
    mock_delete_repo.assert_called_once_with(repository_id=1)


@patch("doc_ai_helper_backend.api.endpoints.repositories.delete_repository")
def test_delete_repository_not_found(mock_delete_repo, client):
    """Test delete repository endpoint with not found error."""
    # Setup mock to raise exception
    mock_delete_repo.side_effect = NotFoundException("Repository not found")

    # Test
    response = client.delete(f"{settings.api_prefix}/repositories/999")

    # Verify
    assert response.status_code == 404
    assert "message" in response.json()
    assert response.json()["message"] == "Repository not found"
