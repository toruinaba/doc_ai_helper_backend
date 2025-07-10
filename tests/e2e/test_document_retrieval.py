"""
Document Retrieval E2E Tests.

This module contains E2E tests focused on document retrieval functionality
across different Git services, verifying basic API functionality without
complex MCP workflows.
"""

import pytest
import logging
from typing import Dict, Any

from tests.e2e.helpers.config import E2EConfig
from tests.e2e.helpers.api_client import BackendAPIClient

logger = logging.getLogger(__name__)


@pytest.mark.e2e
@pytest.mark.asyncio
class TestDocumentRetrieval:
    """
    E2E tests for document retrieval functionality.
    """

    async def test_github_document_retrieval(
        self,
        backend_api_client: BackendAPIClient,
        e2e_config: E2EConfig,
        test_repository_context
    ):
        """Test basic document retrieval from GitHub."""
        if not e2e_config.has_github_config:
            pytest.skip("GitHub configuration not available for E2E tests")

        logger.info("=== Testing GitHub Document Retrieval ===")
        
        # Test README.md retrieval
        document = await backend_api_client.get_document(
            service="github",
            owner=e2e_config.github_owner,
            repo=e2e_config.github_repo,
            path="README.md"
        )
        
        # Verify document structure
        assert document is not None, "Document should not be None"
        assert "content" in document, "Document should have content field"
        assert "metadata" in document, "Document should have metadata field"
        assert "path" in document, "Document should have path field"
        assert document["path"] == "README.md", "Path should match requested path"
        assert document["service"] == "github", "Service should be github"
        assert document["owner"] == e2e_config.github_owner, "Owner should match"
        assert document["repository"] == e2e_config.github_repo, "Repository should match"
        
        # Verify content is not empty
        content = document["content"]
        assert "content" in content, "Content should have content field"
        assert len(content["content"]) > 0, "Content should not be empty"
        
        logger.info(f"✅ Successfully retrieved GitHub document: {document['path']}")
        logger.info(f"Content length: {len(content['content'])} characters")

    async def test_forgejo_document_retrieval(
        self,
        backend_api_client: BackendAPIClient,
        e2e_config: E2EConfig,
        test_repository_context
    ):
        """Test basic document retrieval from Forgejo."""
        if not e2e_config.has_forgejo_config:
            pytest.skip("Forgejo configuration not available for E2E tests")

        logger.info("=== Testing Forgejo Document Retrieval ===")
        
        # Test README.md retrieval
        document = await backend_api_client.get_document(
            service="forgejo",
            owner=e2e_config.forgejo_owner,
            repo=e2e_config.forgejo_repo,
            path="README.md"
        )
        
        # Verify document structure
        assert document is not None, "Document should not be None"
        assert "content" in document, "Document should have content field"
        assert "metadata" in document, "Document should have metadata field"
        assert "path" in document, "Document should have path field"
        assert document["path"] == "README.md", "Path should match requested path"
        assert document["service"] == "forgejo", "Service should be forgejo"
        assert document["owner"] == e2e_config.forgejo_owner, "Owner should match"
        assert document["repository"] == e2e_config.forgejo_repo, "Repository should match"
        
        # Verify content is not empty
        content = document["content"]
        assert "content" in content, "Content should have content field"
        assert len(content["content"]) > 0, "Content should not be empty"
        
        logger.info(f"✅ Successfully retrieved Forgejo document: {document['path']}")
        logger.info(f"Content length: {len(content['content'])} characters")

    async def test_repository_structure_retrieval(
        self,
        backend_api_client: BackendAPIClient,
        e2e_config: E2EConfig,
        test_repository_context
    ):
        """Test repository structure retrieval from available services."""
        tested_services = []
        
        for service in e2e_config.available_services:
            repo_config = e2e_config.get_repository_config(service)
            
            if repo_config["available"]:
                logger.info(f"Testing repository structure retrieval from {service}")
                
                structure = await backend_api_client.get_repository_structure(
                    service=service,
                    owner=repo_config["owner"],
                    repo=repo_config["repo"]
                )
                
                # Verify structure
                assert structure is not None, f"Structure should not be None for {service}"
                assert "tree" in structure, f"Structure should have tree for {service}"
                assert isinstance(structure["tree"], list), f"Tree should be a list for {service}"
                assert len(structure["tree"]) > 0, f"Repository should have some items for {service}"
                
                # Verify we have both files and directories
                files = [item for item in structure["tree"] if item.get("type") == "file"]
                directories = [item for item in structure["tree"] if item.get("type") == "directory"]
                
                assert len(files) > 0, f"Repository should have some files for {service}"
                
                logger.info(f"✅ {service}: {len(files)} files, {len(directories)} directories")
                tested_services.append(service)
        
        assert len(tested_services) > 0, "Should test at least one service"
        logger.info(f"✅ Repository structure retrieval tested for: {', '.join(tested_services)}")

    async def test_document_with_different_refs(
        self,
        backend_api_client: BackendAPIClient,
        e2e_config: E2EConfig
    ):
        """Test document retrieval with different refs (branches/tags)."""
        if not e2e_config.available_services:
            pytest.skip("No Git services configured for E2E tests")

        # Test with the first available service
        service = e2e_config.available_services[0]
        repo_config = e2e_config.get_repository_config(service)
        
        logger.info(f"Testing different refs with {service}")
        
        # Test with main branch (explicit)
        document_main = await backend_api_client.get_document(
            service=service,
            owner=repo_config["owner"],
            repo=repo_config["repo"],
            path="README.md",
            ref="main"
        )
        
        assert document_main is not None, "Document from main branch should exist"
        assert document_main["path"] == "README.md"
        
        # Test with HEAD (should work the same)
        try:
            document_head = await backend_api_client.get_document(
                service=service,
                owner=repo_config["owner"],
                repo=repo_config["repo"],
                path="README.md",
                ref="HEAD"
            )
            
            assert document_head is not None, "Document from HEAD should exist"
            logger.info("✅ Successfully retrieved document with HEAD ref")
        except Exception as e:
            logger.info(f"HEAD ref not supported or failed: {e}")
        
        logger.info(f"✅ Document retrieval with different refs tested for {service}")

    async def test_link_transformation(
        self,
        backend_api_client: BackendAPIClient,
        e2e_config: E2EConfig
    ):
        """Test link transformation functionality in documents."""
        if not e2e_config.available_services:
            pytest.skip("No Git services configured for E2E tests")

        service = e2e_config.available_services[0]
        repo_config = e2e_config.get_repository_config(service)
        
        logger.info(f"Testing link transformation with {service}")
        
        # Get document with link transformation enabled
        document_with_transform = await backend_api_client.get_document(
            service=service,
            owner=repo_config["owner"],
            repo=repo_config["repo"],
            path="README.md",
            transform_links=True
        )
        
        # Get document without link transformation  
        document_without_transform = await backend_api_client.get_document(
            service=service,
            owner=repo_config["owner"],
            repo=repo_config["repo"],
            path="README.md",
            transform_links=False
        )
        
        assert document_with_transform is not None
        assert document_without_transform is not None
        
        # Both should have the same basic structure
        assert document_with_transform["path"] == document_without_transform["path"]
        
        # Content might differ if there are relative links to transform
        content_with = document_with_transform["content"]["content"]
        content_without = document_without_transform["content"]["content"]
        
        logger.info(f"✅ Link transformation tested - with transform: {len(content_with)} chars, without: {len(content_without)} chars")

    async def test_multiple_document_retrieval(
        self,
        backend_api_client: BackendAPIClient,
        e2e_config: E2EConfig
    ):
        """Test retrieving multiple documents from a repository."""
        if not e2e_config.available_services:
            pytest.skip("No Git services configured for E2E tests")

        service = e2e_config.available_services[0]
        repo_config = e2e_config.get_repository_config(service)
        
        logger.info(f"Testing multiple document retrieval with {service}")
        
        # First get repository structure to find available files
        structure = await backend_api_client.get_repository_structure(
            service=service,
            owner=repo_config["owner"],
            repo=repo_config["repo"]
        )
        
        # Find markdown files
        markdown_files = [
            item for item in structure["tree"]
            if item.get("type") == "file" and 
               item.get("name", "").lower().endswith((".md", ".markdown"))
        ]
        
        if len(markdown_files) == 0:
            logger.info("No markdown files found in repository")
            return
        
        # Retrieve up to 3 markdown files
        retrieved_docs = []
        for file_info in markdown_files[:3]:
            file_path = file_info.get("path", file_info.get("name"))
            
            try:
                document = await backend_api_client.get_document(
                    service=service,
                    owner=repo_config["owner"],
                    repo=repo_config["repo"],
                    path=file_path
                )
                
                retrieved_docs.append({
                    "path": file_path,
                    "document": document,
                    "size": len(document["content"]["content"])
                })
                
                logger.info(f"Retrieved {file_path}: {len(document['content']['content'])} chars")
                
            except Exception as e:
                logger.warning(f"Failed to retrieve {file_path}: {e}")
        
        assert len(retrieved_docs) > 0, "Should retrieve at least one document"
        logger.info(f"✅ Successfully retrieved {len(retrieved_docs)} documents")

    async def test_document_metadata_extraction(
        self,
        backend_api_client: BackendAPIClient,
        e2e_config: E2EConfig
    ):
        """Test document metadata extraction."""
        if not e2e_config.available_services:
            pytest.skip("No Git services configured for E2E tests")

        service = e2e_config.available_services[0]
        repo_config = e2e_config.get_repository_config(service)
        
        logger.info(f"Testing document metadata extraction with {service}")
        
        document = await backend_api_client.get_document(
            service=service,
            owner=repo_config["owner"],
            repo=repo_config["repo"],
            path="README.md"
        )
        
        # Verify metadata structure
        assert "metadata" in document, "Document should have metadata"
        metadata = document["metadata"]
        
        # Common metadata fields that should be present
        expected_fields = ["size", "type", "encoding"]
        for field in expected_fields:
            if field in metadata:
                logger.info(f"Metadata {field}: {metadata[field]}")
        
        # Verify some basic metadata properties
        if "size" in metadata:
            assert isinstance(metadata["size"], int), "Size should be an integer"
            assert metadata["size"] > 0, "Size should be positive"
        
        if "type" in metadata:
            assert isinstance(metadata["type"], str), "Type should be a string"
        
        logger.info("✅ Document metadata extraction verified")