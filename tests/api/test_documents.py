"""
Test document-related endpoints.
"""

import pytest

from doc_ai_helper_backend.core.config import settings
from doc_ai_helper_backend.api.endpoints import documents


def test_get_document(client):
    """Test get document endpoint."""
    # Test with mock service
    response = client.get(
        f"{settings.api_prefix}/documents/contents/mock/octocat/Hello-World/README.md"
    )

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["path"] == "README.md"
    assert data["name"] == "README.md"
    assert data["type"] == "markdown"
    assert data["service"] == "mock"
    assert data["owner"] == "octocat"
    assert data["repository"] == "Hello-World"
    assert "content" in data
    assert "metadata" in data
    assert data["content"]["content"].startswith("# Hello World")


def test_get_document_not_found(client):
    """Test get document endpoint with not found error."""
    # Test with non-existent document
    response = client.get(
        f"{settings.api_prefix}/documents/contents/mock/octocat/Hello-World/nonexistent.md"
    )

    # Verify
    assert response.status_code == 404
    assert "message" in response.json()
    assert "not found" in response.json()["message"].lower()


def test_get_repository_structure(client):
    """Test get repository structure endpoint."""
    # Test with mock service
    response = client.get(
        f"{settings.api_prefix}/documents/structure/mock/octocat/Hello-World"
    )

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "mock"
    assert data["owner"] == "octocat"
    assert data["repo"] == "Hello-World"
    assert "tree" in data
    assert len(data["tree"]) >= 3  # At least README.md, docs folder, and docs/index.md

    # Find README.md in tree
    readme = next((item for item in data["tree"] if item["path"] == "README.md"), None)
    assert readme is not None
    assert readme["name"] == "README.md"
    assert readme["type"] == "file"


def test_get_repository_structure_not_found(client):
    """Test get repository structure endpoint with not found error."""
    # Test with non-existent repository
    response = client.get(
        f"{settings.api_prefix}/documents/structure/mock/nonexistent/repo"
    )

    # Verify
    assert response.status_code == 404
    assert "message" in response.json()
    assert "not found" in response.json()["message"].lower()


def test_unsupported_git_service(client):
    """Test unsupported Git service."""
    # Test accessing endpoint with unsupported Git service
    response = client.get(
        f"{settings.api_prefix}/documents/contents/gitlab/octocat/Hello-World/README.md"
    )

    # Verify not found or error response
    assert response.status_code == 404
    assert (
        "unsupported" in response.json()["message"].lower()
        or "not found" in response.json()["message"].lower()
    )
