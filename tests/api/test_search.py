"""
Test search-related endpoints.
"""

import pytest
from unittest.mock import patch

from doc_ai_helper_backend.core.config import settings
from doc_ai_helper_backend.core.exceptions import NotFoundException, GitServiceException
from tests.api.mock_services import mock_search_service


@pytest.fixture
def mock_search_results():
    """Create mock search results."""
    return {
        "total": 2,
        "offset": 0,
        "limit": 10,
        "query": "test query",
        "results": [
            {
                "path": "docs/README.md",
                "name": "README.md",
                "type": "markdown",
                "repository": "test-repo",
                "owner": "test-owner",
                "service": "github",
                "score": 0.95,
                "highlight": "This is a <em>test</em> document",
                "metadata": {"size": 1024, "last_modified": "2025-06-12T10:00:00Z"},
            },
            {
                "path": "docs/API.md",
                "name": "API.md",
                "type": "markdown",
                "repository": "test-repo",
                "owner": "test-owner",
                "service": "github",
                "score": 0.85,
                "highlight": "API <em>test</em> documentation",
                "metadata": {"size": 2048, "last_modified": "2025-06-10T10:00:00Z"},
            },
        ],
        "execution_time_ms": 15.5,
    }


@patch("doc_ai_helper_backend.api.endpoints.search.search_repository")
def test_search_repository(mock_search, client, mock_search_results):
    """Test search repository endpoint."""
    # Setup mock
    mock_search.return_value = mock_search_results

    # Search query
    search_query = {
        "query": "test query",
        "limit": 10,
        "offset": 0,
        "file_extensions": [".md", ".txt"],
    }

    # Test
    response = client.post(
        f"{settings.api_prefix}/search/github/test-owner/test-repo", json=search_query
    )

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["query"] == "test query"
    assert len(data["results"]) == 2
    assert data["results"][0]["path"] == "docs/README.md"
    assert data["results"][0]["score"] == 0.95
    assert "highlight" in data["results"][0]

    # Verify mock was called with correct parameters
    mock_search.assert_called_once_with(
        search_query=pytest.approx(search_query),
        service="github",
        owner="test-owner",
        repo="test-repo",
    )


@patch("doc_ai_helper_backend.api.endpoints.search.search_repository")
def test_search_repository_empty_results(mock_search, client):
    """Test search repository endpoint with empty results."""
    # Setup mock
    empty_results = {
        "total": 0,
        "offset": 0,
        "limit": 10,
        "query": "nonexistent",
        "results": [],
        "execution_time_ms": 5.2,
    }
    mock_search.return_value = empty_results

    # Search query
    search_query = {"query": "nonexistent", "limit": 10, "offset": 0}

    # Test
    response = client.post(
        f"{settings.api_prefix}/search/github/test-owner/test-repo", json=search_query
    )

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["results"]) == 0


@patch("doc_ai_helper_backend.api.endpoints.search.search_repository")
def test_search_repository_not_found(mock_search, client):
    """Test search repository endpoint with not found error."""
    # Setup mock to raise exception
    mock_search.side_effect = NotFoundException("Repository not found")

    # Search query
    search_query = {"query": "test"}

    # Test
    response = client.post(
        f"{settings.api_prefix}/search/github/test-owner/nonexistent", json=search_query
    )

    # Verify
    assert response.status_code == 404
    assert "message" in response.json()
    assert response.json()["message"] == "Repository not found"


@patch("doc_ai_helper_backend.api.endpoints.search.search_repository")
def test_search_repository_service_error(mock_search, client):
    """Test search repository endpoint with service error."""
    # Setup mock to raise exception
    mock_search.side_effect = GitServiceException("API rate limit exceeded")

    # Search query
    search_query = {"query": "test"}

    # Test
    response = client.post(
        f"{settings.api_prefix}/search/github/test-owner/test-repo", json=search_query
    )

    # Verify
    assert response.status_code == 500
    assert "message" in response.json()
    assert response.json()["message"] == "API rate limit exceeded"


def test_search_repository_validation_error(client):
    """Test search repository endpoint with validation error."""
    # Invalid search query missing required 'query' field
    search_query = {"limit": 10, "offset": 0}

    # Test
    response = client.post(
        f"{settings.api_prefix}/search/github/test-owner/test-repo", json=search_query
    )

    # Verify
    assert response.status_code == 422  # Validation error
    assert "detail" in response.json()
