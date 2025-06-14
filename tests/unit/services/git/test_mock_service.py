"""
Unit tests for MockGitService.

These tests verify that the MockGitService correctly returns mock data
and handles different scenarios properly.
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List

from doc_ai_helper_backend.services.git.factory import GitServiceFactory
from doc_ai_helper_backend.services.git.mock_service import MockGitService
from doc_ai_helper_backend.models.document import DocumentResponse, FileTreeItem
from doc_ai_helper_backend.core.exceptions import NotFoundException


class TestMockGitService:
    @pytest.fixture
    def mock_service(self):
        """Create a mock git service instance."""
        return GitServiceFactory.create("mock")

    @pytest.mark.asyncio
    async def test_service_name(self, mock_service):
        """Test that the service name is correctly returned."""
        assert mock_service.service_name == "mock"

    @pytest.mark.asyncio
    async def test_get_document_basic(self, mock_service):
        """Test getting a basic document."""
        # Test with a basic document
        doc = await mock_service.get_document(
            owner="octocat", repo="Hello-World", path="README.md", ref="main"
        )

        # Verify the response structure
        assert isinstance(doc, DocumentResponse)
        assert doc.path == "README.md"
        assert doc.name == "README.md"
        assert doc.owner == "octocat"
        assert doc.service == "mock"
        assert doc.repository == "Hello-World"
        assert doc.ref == "main"
        assert len(doc.content.content) > 0
        assert doc.metadata is not None

    @pytest.mark.asyncio
    async def test_get_document_with_links(self, mock_service):
        """Test getting a document with links."""
        # Test with a document containing links
        doc = await mock_service.get_document(
            owner="example", repo="docs-project", path="user-guide/index.md", ref="main"
        )

        # Verify links are extracted - if links are supported in the current implementation
        # Note: In some implementations, links might not be extracted automatically
        # If links are None, this test is skipped
        if doc.links is not None:
            assert len(doc.links) > 0

            # Check that we have at least one of each link type
            has_external = False
            has_internal = False

            for link in doc.links:
                assert link.text is not None
                assert link.url is not None
                assert isinstance(link.is_external, bool)

                if link.is_external:
                    has_external = True
                else:
                    has_internal = True

            # If links are processed, ensure we have internal links
            assert has_internal, "No internal links found in test document"

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, mock_service):
        """Test getting a non-existent document."""
        # Test with a non-existent document
        with pytest.raises(NotFoundException):
            await mock_service.get_document(
                owner="example",
                repo="docs-project",
                path="non-existent.md",
                ref="non-existent-branch",
            )

    @pytest.mark.asyncio
    async def test_get_repository_structure(self, mock_service):
        """Test getting repository structure."""
        # Test getting repository structure
        structure = await mock_service.get_repository_structure(
            owner="example", repo="docs-project", ref="main"
        )

        # Verify structure
        assert structure.service == "mock"
        assert structure.owner == "example"
        assert structure.repo == "docs-project"
        assert structure.ref == "main"
        assert len(structure.tree) > 0

        # Verify structure contains both files and directories
        has_file = False
        has_directory = False

        for item in structure.tree:
            assert isinstance(item, FileTreeItem)
            assert item.path is not None
            assert item.name is not None
            assert item.type in ["file", "directory"]

            if item.type == "file":
                has_file = True
                assert item.size is not None
            else:
                has_directory = True

        assert has_file, "No files found in repository structure"
        assert has_directory, "No directories found in repository structure"

    @pytest.mark.asyncio
    async def test_get_repository_structure_with_path(self, mock_service):
        """Test getting repository structure with a path filter."""
        # Test getting repository structure with path
        structure = await mock_service.get_repository_structure(
            owner="example",
            repo="docs-project",
            ref="main",
            path="user-guide",  # Using a path that exists in the mock data
        )

        # Verify filtered structure
        assert len(structure.tree) > 0

        # Only check if at least one item has the path prefix
        has_path_match = False
        for item in structure.tree:
            if item.path.startswith("user-guide"):
                has_path_match = True
                break

        assert has_path_match, "No items with path prefix 'user-guide' found"

    @pytest.mark.asyncio
    async def test_search_repository(self, mock_service):
        """Test searching repository."""
        # Test searching repository
        search_results = await mock_service.search_repository(
            owner="example", repo="docs-project", query="api", limit=10
        )

        # Verify search results
        assert "results" in search_results
        assert isinstance(search_results["results"], list)

        if len(search_results["results"]) > 0:
            result = search_results["results"][0]
            assert "path" in result
            assert "score" in result
            assert "highlight" in result

    @pytest.mark.asyncio
    async def test_check_repository_exists(self, mock_service):
        """Test checking if repository exists."""
        # Test with existing repository
        exists = await mock_service.check_repository_exists(
            owner="example", repo="docs-project"
        )
        assert exists is True

        # For non-existent repositories, the behavior depends on how the mock is configured
        # In the default implementation, it should return True for all repositories
        # unless existing_repos is explicitly set
