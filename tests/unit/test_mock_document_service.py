"""
Unit tests for the MockDocumentService class.
"""

import pytest
from datetime import datetime

from doc_ai_helper_backend.core.exceptions import NotFoundException
from doc_ai_helper_backend.models.document import DocumentType
from tests.api.mock_document_service import (
    MockDocumentService,
    create_mock_document_service,
)
from tests.api.mock_git_service import create_mock_git_service


@pytest.fixture
def mock_document_service():
    """Fixture to create a mock document service with test data."""
    return create_mock_document_service()


@pytest.mark.asyncio
async def test_get_document_existing(mock_document_service):
    """Test getting an existing document."""
    # Get README.md
    document = await mock_document_service.get_document(
        service="github", owner="octocat", repo="Hello-World", path="README.md"
    )

    # Verify document data
    assert document.path == "README.md"
    assert document.name == "README.md"
    assert document.type == DocumentType.MARKDOWN
    assert document.service == "github"
    assert document.owner == "octocat"
    assert document.repository == "Hello-World"
    assert document.content.content.startswith("# Hello World")
    assert document.metadata.size == 42
    assert (
        str(document.metadata.html_url)
        == "https://github.com/octocat/Hello-World/blob/main/README.md"
    )


@pytest.mark.asyncio
async def test_get_document_nonexistent(mock_document_service):
    """Test getting a nonexistent document."""
    # Try to get a nonexistent document
    with pytest.raises(NotFoundException) as exc_info:
        await mock_document_service.get_document(
            service="github", owner="octocat", repo="Hello-World", path="nonexistent.md"
        )

    # Verify error message
    assert "Document not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_document_nonexistent_repo(mock_document_service):
    """Test getting a document from a nonexistent repository."""
    # Try to get a document from a nonexistent repository
    with pytest.raises(NotFoundException) as exc_info:
        await mock_document_service.get_document(
            service="github", owner="nonexistent", repo="repo", path="README.md"
        )

    # Verify error message
    assert "Repository not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_repository_structure_existing(mock_document_service):
    """Test getting an existing repository structure."""
    # Get repository structure
    structure = await mock_document_service.get_repository_structure(
        service="github", owner="octocat", repo="Hello-World"
    )

    # Verify structure data
    assert structure.service == "github"
    assert structure.owner == "octocat"
    assert structure.repo == "Hello-World"
    assert structure.ref == "main"

    # Verify tree
    assert (
        len(structure.tree) >= 3
    )  # At least README.md, docs folder, and docs/index.md

    # Find README.md in tree
    readme = next((item for item in structure.tree if item.path == "README.md"), None)
    assert readme is not None
    assert readme.name == "README.md"
    assert readme.type == "file"
    assert readme.size == 42
    assert (
        str(readme.html_url)
        == "https://github.com/octocat/Hello-World/blob/main/README.md"
    )


@pytest.mark.asyncio
async def test_get_repository_structure_nonexistent(mock_document_service):
    """Test getting a nonexistent repository structure."""
    # Try to get structure of a nonexistent repository
    with pytest.raises(NotFoundException) as exc_info:
        await mock_document_service.get_repository_structure(
            service="github", owner="nonexistent", repo="repo"
        )

    # Verify error message
    assert "Repository not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_search_repository_existing(mock_document_service):
    """Test searching in an existing repository."""
    # Search for "documentation"
    results = await mock_document_service.search_repository(
        service="github",
        owner="octocat",
        repo="Hello-World",
        query="documentation",
        limit=10,
    )

    # Verify results
    assert "results" in results
    assert results["service"] == "github"
    assert results["owner"] == "octocat"
    assert results["repo"] == "Hello-World"
    assert results["query"] == "documentation"
    assert results["limit"] == 10

    results_list = results["results"]
    assert len(results_list) >= 2  # At least 2 results

    # Verify first result
    first_result = results_list[0]
    assert first_result["path"] == "docs/index.md"
    assert first_result["name"] == "index.md"
    assert (
        first_result["html_url"]
        == "https://github.com/octocat/Hello-World/blob/main/docs/index.md"
    )
    assert first_result["score"] == 0.9
    assert "documentation" in first_result["highlight"].lower()
    assert first_result["repository"]["name"] == "Hello-World"
    assert first_result["repository"]["owner"] == "octocat"


@pytest.mark.asyncio
async def test_search_repository_nonexistent(mock_document_service):
    """Test searching in a nonexistent repository."""
    # Try to search in a nonexistent repository
    with pytest.raises(NotFoundException) as exc_info:
        await mock_document_service.search_repository(
            service="github", owner="nonexistent", repo="repo", query="documentation"
        )

    # Verify error message
    assert "Repository not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_check_repository_exists(mock_document_service):
    """Test checking if a repository exists."""
    # Check existing repository
    exists = await mock_document_service.check_repository_exists(
        service="github", owner="octocat", repo="Hello-World"
    )
    assert exists is True

    # Check nonexistent repository
    exists = await mock_document_service.check_repository_exists(
        service="github", owner="nonexistent", repo="repo"
    )
    assert exists is False


@pytest.mark.asyncio
async def test_custom_mock_document_service():
    """Test creating a custom mock document service."""
    # Create a custom mock Git service
    custom_git_mock = create_mock_git_service()

    # Add custom document
    custom_git_mock.documents["custom/repo/test.md@main"] = {
        "content": "# Custom Test\n\nThis is a custom test file.",
        "metadata": {
            "size": 40,
            "last_modified": datetime(2023, 1, 1),
            "content_type": "text/markdown",
            "sha": "custom123",
            "download_url": "https://example.com/custom/repo/test.md",
            "html_url": "https://example.com/custom/repo/blob/main/test.md",
            "raw_url": "https://example.com/custom/repo/raw/main/test.md",
            "encoding": "utf-8",
        },
    }

    # Add custom repository to existing repos
    custom_git_mock.existing_repos.append("custom/repo")

    # Create custom document service with custom Git service
    custom_doc_service = MockDocumentService(mock_git_service=custom_git_mock)

    # Get custom document
    document = await custom_doc_service.get_document(
        service="github", owner="custom", repo="repo", path="test.md"
    )

    # Verify document
    assert document.path == "test.md"
    assert document.name == "test.md"
    assert document.content.content.startswith("# Custom Test")
    assert document.metadata.sha == "custom123"

    # Check existence
    exists = await custom_doc_service.check_repository_exists(
        service="github", owner="custom", repo="repo"
    )
    assert exists is True
