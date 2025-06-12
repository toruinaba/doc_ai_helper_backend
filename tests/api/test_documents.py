"""
Test document-related endpoints.
"""

import pytest
from datetime import datetime

from doc_ai_helper_backend.core.config import settings
from doc_ai_helper_backend.core.exceptions import NotFoundException
from doc_ai_helper_backend.models.document import DocumentType
from tests.api.mock_services import mock_document_service


@pytest.fixture
def mock_document_data():
    """Create mock document data."""
    return {
        "path": "docs/README.md",
        "name": "README.md",
        "type": DocumentType.MARKDOWN,
        "metadata": {
            "size": 1024,
            "last_modified": datetime.now().isoformat(),
            "content_type": "text/markdown",
            "sha": "abc123",
            "download_url": "https://example.com/download",
            "html_url": "https://example.com/html",
            "raw_url": "https://example.com/raw",
        },
        "content": {
            "content": "# Test Document\n\nThis is a test document.",
            "encoding": "utf-8",
        },
        "repository": "test-repo",
        "owner": "test-owner",
        "service": "github",
        "ref": "main",
    }


def test_get_document(client, mock_document_data):
    """Test get document endpoint."""
    # Setup mock
    mock_document_service.get_document.return_value = mock_document_data

    # Test
    response = client.get(
        f"{settings.api_prefix}/documents/github/test-owner/test-repo/docs/README.md"
    )

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["path"] == "docs/README.md"
    assert data["name"] == "README.md"
    assert data["type"] == "markdown"
    assert "content" in data
    assert "metadata" in data

    # Verify mock was called with correct parameters
    mock_document_service.get_document.assert_called_once_with(
        service="github",
        owner="test-owner",
        repo="test-repo",
        path="docs/README.md",
        ref="main",
    )


def test_get_document_not_found(client):
    """Test get document endpoint with not found error."""
    # Setup mock to raise exception
    mock_document_service.get_document.side_effect = NotFoundException(
        "Document not found"
    )

    # Test
    response = client.get(
        f"{settings.api_prefix}/documents/github/test-owner/test-repo/not-found.md"
    )

    # Verify
    assert response.status_code == 404
    assert "message" in response.json()
    assert response.json()["message"] == "Document not found"


def test_get_repository_structure(client):
    """Test get repository structure endpoint."""
    # Setup mock
    mock_structure = {
        "service": "github",
        "owner": "test-owner",
        "repo": "test-repo",
        "ref": "main",
        "tree": [
            {
                "path": "README.md",
                "name": "README.md",
                "type": "file",
                "size": 1024,
                "sha": "abc123",
                "download_url": "https://example.com/download",
                "html_url": "https://example.com/html",
                "git_url": "https://example.com/git",
            },
            {
                "path": "docs",
                "name": "docs",
                "type": "directory",
                "sha": "def456",
                "html_url": "https://example.com/html/docs",
                "git_url": "https://example.com/git/docs",
            },
        ],
        "last_updated": datetime.now().isoformat(),
    }
    mock_document_service.get_repository_structure.return_value = mock_structure

    # Test
    response = client.get(
        f"{settings.api_prefix}/documents/structure/github/test-owner/test-repo"
    )

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "github"
    assert data["owner"] == "test-owner"
    assert data["repo"] == "test-repo"
    assert "tree" in data
    assert len(data["tree"]) == 2

    # Verify mock was called with correct parameters
    mock_document_service.get_repository_structure.assert_called_once_with(
        service="github", owner="test-owner", repo="test-repo", ref="main", path=""
    )


def test_get_repository_structure_not_found(client):
    """Test get repository structure endpoint with not found error."""
    # Setup mock to raise exception
    mock_document_service.get_repository_structure.side_effect = NotFoundException(
        "Repository not found"
    )

    # Test
    response = client.get(
        f"{settings.api_prefix}/documents/structure/github/test-owner/not-found"
    )

    # Verify
    assert response.status_code == 404
    assert "message" in response.json()
    assert response.json()["message"] == "Repository not found"
