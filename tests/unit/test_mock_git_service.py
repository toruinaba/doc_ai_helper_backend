"""
Unit tests for the MockGitService class.
"""

import pytest
from datetime import datetime

from doc_ai_helper_backend.core.exceptions import NotFoundException
from doc_ai_helper_backend.models.document import DocumentType, FileTreeItem
from tests.api.mock_git_service import MockGitService, create_mock_git_service


@pytest.fixture
def mock_git_service():
    """Fixture to create a mock Git service with test data."""
    return create_mock_git_service()


@pytest.mark.asyncio
async def test_get_service_name(mock_git_service):
    """Test getting service name."""
    assert mock_git_service.service_name == "github"
    assert mock_git_service._get_service_name() == "github"


@pytest.mark.asyncio
async def test_get_document_existing(mock_git_service):
    """Test getting an existing document."""
    # Get README.md
    document = await mock_git_service.get_document(
        owner="octocat", repo="Hello-World", path="README.md"
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
async def test_get_document_nonexistent(mock_git_service):
    """Test getting a nonexistent document."""
    # Try to get a nonexistent document
    with pytest.raises(NotFoundException) as exc_info:
        await mock_git_service.get_document(
            owner="octocat", repo="Hello-World", path="nonexistent.md"
        )

    # Verify error message
    assert "Document not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_document_nonexistent_repo(mock_git_service):
    """Test getting a document from a nonexistent repository."""
    # Try to get a document from a nonexistent repository
    with pytest.raises(NotFoundException) as exc_info:
        await mock_git_service.get_document(
            owner="nonexistent", repo="repo", path="README.md"
        )

    # Verify error message
    assert "Repository not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_repository_structure_existing(mock_git_service):
    """Test getting an existing repository structure."""
    # Get repository structure
    structure = await mock_git_service.get_repository_structure(
        owner="octocat", repo="Hello-World"
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

    # Find docs folder in tree
    docs_folder = next((item for item in structure.tree if item.path == "docs"), None)
    assert docs_folder is not None
    assert docs_folder.name == "docs"
    assert docs_folder.type == "directory"
    assert docs_folder.size is None

    # Find docs/index.md in tree
    docs_index = next(
        (item for item in structure.tree if item.path == "docs/index.md"), None
    )
    assert docs_index is not None
    assert docs_index.name == "index.md"
    assert docs_index.type == "file"
    assert docs_index.size == 47


@pytest.mark.asyncio
async def test_get_repository_structure_nonexistent(mock_git_service):
    """Test getting a nonexistent repository structure."""
    # Try to get structure of a nonexistent repository
    with pytest.raises(NotFoundException) as exc_info:
        await mock_git_service.get_repository_structure(
            owner="nonexistent", repo="repo"
        )

    # Verify error message
    assert "Repository not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_search_repository_existing(mock_git_service):
    """Test searching in an existing repository."""
    # Search for "documentation"
    results = await mock_git_service.search_repository(
        owner="octocat", repo="Hello-World", query="documentation", limit=10
    )

    # Verify results
    assert "results" in results
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
async def test_search_repository_nonexistent(mock_git_service):
    """Test searching in a nonexistent repository."""
    # Try to search in a nonexistent repository
    with pytest.raises(NotFoundException) as exc_info:
        await mock_git_service.search_repository(
            owner="nonexistent", repo="repo", query="documentation"
        )

    # Verify error message
    assert "Repository not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_check_repository_exists(mock_git_service):
    """Test checking if a repository exists."""
    # Check existing repository
    exists = await mock_git_service.check_repository_exists(
        owner="octocat", repo="Hello-World"
    )
    assert exists is True

    # Check nonexistent repository
    exists = await mock_git_service.check_repository_exists(
        owner="nonexistent", repo="repo"
    )
    assert exists is False


@pytest.mark.asyncio
async def test_custom_mock_git_service():
    """Test creating a custom mock Git service."""
    # Create a custom mock Git service
    custom_mock = MockGitService(
        service_name="custom",
        documents={
            "test/repo/file.md@main": {
                "content": "# Test\n\nThis is a test file.",
                "metadata": {
                    "size": 30,
                    "last_modified": datetime(2023, 1, 1),
                    "content_type": "text/markdown",
                    "sha": "abcdef",
                    "download_url": "https://example.com/test/repo/file.md",
                    "html_url": "https://example.com/test/repo/blob/main/file.md",
                    "raw_url": "https://example.com/test/repo/raw/main/file.md",
                    "encoding": "utf-8",
                },
            }
        },
        structures={
            "test/repo@main": {
                "tree": [
                    {
                        "path": "file.md",
                        "name": "file.md",
                        "type": "file",
                        "size": 30,
                        "sha": "abcdef",
                        "download_url": "https://example.com/test/repo/file.md",
                        "html_url": "https://example.com/test/repo/blob/main/file.md",
                        "git_url": "https://example.com/api/repos/test/repo/git/blobs/abcdef",
                    }
                ],
                "last_updated": datetime(2023, 1, 1),
            }
        },
        search_results={
            "test/repo:test": {
                "results": [
                    {
                        "path": "file.md",
                        "name": "file.md",
                        "html_url": "https://example.com/test/repo/blob/main/file.md",
                        "score": 1.0,
                        "highlight": "This is a <em>test</em> file.",
                        "repository": {
                            "name": "repo",
                            "owner": "test",
                        },
                    }
                ]
            }
        },
        existing_repos=["test/repo"],
    )

    # Verify service name
    assert custom_mock.service_name == "custom"

    # Get document
    document = await custom_mock.get_document(owner="test", repo="repo", path="file.md")
    assert document.path == "file.md"
    assert document.content.content == "# Test\n\nThis is a test file."

    # Get structure
    structure = await custom_mock.get_repository_structure(owner="test", repo="repo")
    assert len(structure.tree) == 1
    assert structure.tree[0].path == "file.md"

    # Search
    results = await custom_mock.search_repository(
        owner="test", repo="repo", query="test"
    )
    assert len(results["results"]) == 1
    assert results["results"][0]["path"] == "file.md"

    # Check existence
    exists = await custom_mock.check_repository_exists(owner="test", repo="repo")
    assert exists is True

    # Check nonexistence
    exists = await custom_mock.check_repository_exists(owner="nonexistent", repo="repo")
    assert exists is False


@pytest.mark.asyncio
async def test_detect_document_type():
    """Test detecting document type from file extension."""
    mock_service = create_mock_git_service()

    # Test Markdown
    assert mock_service.detect_document_type("test.md") == DocumentType.MARKDOWN

    # Test Quarto
    assert mock_service.detect_document_type("test.qmd") == DocumentType.QUARTO

    # Test HTML
    assert mock_service.detect_document_type("test.html") == DocumentType.HTML

    # Test other
    assert mock_service.detect_document_type("test.txt") == DocumentType.OTHER
    assert mock_service.detect_document_type("test.py") == DocumentType.OTHER


@pytest.mark.asyncio
async def test_build_document_response():
    """Test building document response."""
    mock_service = create_mock_git_service()

    # Build response
    response = mock_service.build_document_response(
        owner="test",
        repo="repo",
        path="docs/file.md",
        ref="main",
        content="# Test\n\nThis is a test file.",
        metadata={
            "size": 30,
            "last_modified": datetime(2023, 1, 1),
            "content_type": "text/markdown",
            "sha": "abcdef",
            "download_url": "https://example.com/test/repo/file.md",
            "html_url": "https://example.com/test/repo/blob/main/file.md",
            "raw_url": "https://example.com/test/repo/raw/main/file.md",
            "encoding": "utf-8",
        },
    )

    # Verify response
    assert response.path == "docs/file.md"
    assert response.name == "file.md"
    assert response.type == DocumentType.MARKDOWN
    assert response.service == "github"
    assert response.owner == "test"
    assert response.repository == "repo"
    assert response.ref == "main"
    assert response.content.content == "# Test\n\nThis is a test file."
    assert response.content.encoding == "utf-8"
    assert response.metadata.size == 30
    assert response.metadata.content_type == "text/markdown"
    assert response.metadata.sha == "abcdef"
    assert (
        str(response.metadata.download_url) == "https://example.com/test/repo/file.md"
    )
    assert (
        str(response.metadata.html_url)
        == "https://example.com/test/repo/blob/main/file.md"
    )
    assert (
        str(response.metadata.raw_url)
        == "https://example.com/test/repo/raw/main/file.md"
    )
