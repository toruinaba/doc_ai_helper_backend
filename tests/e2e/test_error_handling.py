"""
Error Handling E2E Tests.

This module contains E2E tests focused on error handling scenarios
across the API, ensuring graceful handling of various failure conditions.
"""

import pytest
import logging
from typing import Dict, Any

from tests.e2e.helpers.config import E2EConfig
from tests.e2e.helpers.api_client import BackendAPIClient

logger = logging.getLogger(__name__)


@pytest.mark.e2e
@pytest.mark.asyncio
class TestErrorHandling:
    """
    E2E tests for error handling scenarios.
    """

    async def test_invalid_repository_error(
        self,
        backend_api_client: BackendAPIClient,
        e2e_config: E2EConfig
    ):
        """Test error handling for invalid repository access."""
        if not e2e_config.available_services:
            pytest.skip("No Git services configured for E2E tests")

        service = e2e_config.available_services[0]
        repo_config = e2e_config.get_repository_config(service)
        
        logger.info(f"Testing invalid repository error handling with {service}")
        
        # Try to access non-existent repository
        with pytest.raises(Exception) as exc_info:
            await backend_api_client.get_document(
                service=service,
                owner=repo_config["owner"],
                repo="non-existent-repo-12345",
                path="README.md"
            )
        
        logger.info(f"✅ Expected error occurred for invalid repository: {exc_info.value}")
        
        # Verify the error is related to repository access
        error_str = str(exc_info.value).lower()
        assert any(keyword in error_str for keyword in ["404", "not found", "repository"]), \
            f"Error should indicate repository not found: {exc_info.value}"

    async def test_invalid_file_path_error(
        self,
        backend_api_client: BackendAPIClient, 
        e2e_config: E2EConfig
    ):
        """Test error handling for invalid file path."""
        if not e2e_config.available_services:
            pytest.skip("No Git services configured for E2E tests")

        service = e2e_config.available_services[0]
        repo_config = e2e_config.get_repository_config(service)
        
        logger.info(f"Testing invalid file path error handling with {service}")
        
        # Try to access non-existent file
        with pytest.raises(Exception) as exc_info:
            await backend_api_client.get_document(
                service=service,
                owner=repo_config["owner"],
                repo=repo_config["repo"],
                path="non-existent-file-12345.md"
            )
        
        logger.info(f"✅ Expected error occurred for invalid file path: {exc_info.value}")
        
        # Verify the error is related to file not found
        error_str = str(exc_info.value).lower()
        assert any(keyword in error_str for keyword in ["404", "not found", "file"]), \
            f"Error should indicate file not found: {exc_info.value}"

    async def test_invalid_service_error(
        self,
        backend_api_client: BackendAPIClient,
        e2e_config: E2EConfig
    ):
        """Test error handling for invalid Git service."""
        logger.info("Testing invalid service error handling")
        
        # Try to use non-existent service
        with pytest.raises(Exception) as exc_info:
            await backend_api_client.get_document(
                service="invalid-service-12345",
                owner="test-owner",
                repo="test-repo",
                path="README.md"
            )
        
        logger.info(f"✅ Expected error occurred for invalid service: {exc_info.value}")
        
        # Error could be validation error or service not found
        error_str = str(exc_info.value).lower()
        assert any(keyword in error_str for keyword in ["400", "404", "invalid", "service", "validation"]), \
            f"Error should indicate invalid service: {exc_info.value}"

    async def test_malformed_llm_request_error(
        self,
        backend_api_client: BackendAPIClient,
        e2e_config: E2EConfig
    ):
        """Test error handling for malformed LLM requests."""
        logger.info("Testing malformed LLM request error handling")
        
        # Test with empty prompt
        with pytest.raises(Exception) as exc_info:
            await backend_api_client.query_llm(
                prompt="",  # Empty prompt should cause validation error
                provider=e2e_config.llm_provider
            )
        
        logger.info(f"✅ Expected error occurred for empty prompt: {exc_info.value}")
        
        # Verify it's a validation error
        error_str = str(exc_info.value).lower()
        assert any(keyword in error_str for keyword in ["400", "422", "validation", "invalid", "prompt"]), \
            f"Error should indicate validation failure: {exc_info.value}"

    async def test_repository_structure_error(
        self,
        backend_api_client: BackendAPIClient,
        e2e_config: E2EConfig
    ):
        """Test error handling for repository structure requests."""
        if not e2e_config.available_services:
            pytest.skip("No Git services configured for E2E tests")

        service = e2e_config.available_services[0]
        
        logger.info(f"Testing repository structure error handling with {service}")
        
        # Try to get structure of non-existent repository
        with pytest.raises(Exception) as exc_info:
            await backend_api_client.get_repository_structure(
                service=service,
                owner="non-existent-owner-12345",
                repo="non-existent-repo-12345"
            )
        
        logger.info(f"✅ Expected error occurred for repository structure: {exc_info.value}")
        
        # Verify the error indicates repository not found
        error_str = str(exc_info.value).lower()
        assert any(keyword in error_str for keyword in ["404", "not found", "repository"]), \
            f"Error should indicate repository not found: {exc_info.value}"

    async def test_invalid_ref_error(
        self,
        backend_api_client: BackendAPIClient,
        e2e_config: E2EConfig
    ):
        """Test error handling for invalid branch/tag references."""
        if not e2e_config.available_services:
            pytest.skip("No Git services configured for E2E tests")

        service = e2e_config.available_services[0]
        repo_config = e2e_config.get_repository_config(service)
        
        logger.info(f"Testing invalid ref error handling with {service}")
        
        # Try to access document with non-existent branch/tag
        with pytest.raises(Exception) as exc_info:
            await backend_api_client.get_document(
                service=service,
                owner=repo_config["owner"],
                repo=repo_config["repo"],
                path="README.md",
                ref="non-existent-branch-12345"
            )
        
        logger.info(f"✅ Expected error occurred for invalid ref: {exc_info.value}")
        
        # Verify the error is related to branch/ref not found
        error_str = str(exc_info.value).lower()
        assert any(keyword in error_str for keyword in ["404", "not found", "branch", "ref", "reference"]), \
            f"Error should indicate ref not found: {exc_info.value}"

    async def test_api_server_availability(
        self,
        backend_api_client: BackendAPIClient
    ):
        """Test API server availability and health check."""
        logger.info("Testing API server health check")
        
        # Health check should work
        is_healthy = await backend_api_client.health_check()
        assert is_healthy, "API server should be healthy"
        
        logger.info("✅ API server health check passed")

    async def test_timeout_handling(
        self,
        e2e_config: E2EConfig
    ):
        """Test timeout handling with short timeout."""
        logger.info("Testing timeout handling")
        
        # Create client with very short timeout
        from tests.e2e.helpers.api_client import BackendAPIClient
        
        async with BackendAPIClient(
            base_url=e2e_config.api_base_url,
            timeout=0.001  # 1ms timeout - should cause timeout for most requests
        ) as short_timeout_client:
            
            # This should timeout
            with pytest.raises(Exception) as exc_info:
                await short_timeout_client.health_check()
            
            logger.info(f"✅ Expected timeout error occurred: {exc_info.value}")
            
            # Verify it's a timeout-related error
            error_str = str(exc_info.value).lower()
            assert any(keyword in error_str for keyword in ["timeout", "timed out", "time out"]), \
                f"Error should indicate timeout: {exc_info.value}"

    async def test_invalid_owner_error(
        self,
        backend_api_client: BackendAPIClient,
        e2e_config: E2EConfig
    ):
        """Test error handling for invalid repository owner."""
        if not e2e_config.available_services:
            pytest.skip("No Git services configured for E2E tests")

        service = e2e_config.available_services[0]
        repo_config = e2e_config.get_repository_config(service)
        
        logger.info(f"Testing invalid owner error handling with {service}")
        
        # Try to access repository with non-existent owner
        with pytest.raises(Exception) as exc_info:
            await backend_api_client.get_document(
                service=service,
                owner="non-existent-owner-98765",
                repo=repo_config["repo"],
                path="README.md"
            )
        
        logger.info(f"✅ Expected error occurred for invalid owner: {exc_info.value}")
        
        # Verify the error indicates owner/repository not found
        error_str = str(exc_info.value).lower()
        assert any(keyword in error_str for keyword in ["404", "not found", "owner", "repository"]), \
            f"Error should indicate owner/repository not found: {exc_info.value}"

    async def test_llm_provider_error(
        self,
        backend_api_client: BackendAPIClient
    ):
        """Test error handling for invalid LLM provider."""
        logger.info("Testing invalid LLM provider error handling")
        
        # Try to use non-existent LLM provider
        with pytest.raises(Exception) as exc_info:
            await backend_api_client.query_llm(
                prompt="Test prompt",
                provider="invalid-provider-12345"
            )
        
        logger.info(f"✅ Expected error occurred for invalid LLM provider: {exc_info.value}")
        
        # Verify the error indicates invalid provider
        error_str = str(exc_info.value).lower()
        assert any(keyword in error_str for keyword in ["400", "404", "invalid", "provider", "validation"]), \
            f"Error should indicate invalid provider: {exc_info.value}"

    async def test_error_response_format(
        self,
        backend_api_client: BackendAPIClient,
        e2e_config: E2EConfig
    ):
        """Test that error responses have consistent format."""
        if not e2e_config.available_services:
            pytest.skip("No Git services configured for E2E tests")

        service = e2e_config.available_services[0]
        
        logger.info("Testing error response format consistency")
        
        # Generate a predictable error
        try:
            await backend_api_client.get_document(
                service=service,
                owner="test-owner",
                repo="non-existent-repo",
                path="README.md"
            )
            assert False, "Should have raised an exception"
        except Exception as e:
            # The error should be informative
            error_str = str(e)
            assert len(error_str) > 0, "Error message should not be empty"
            
            # Should contain helpful information
            assert any(keyword in error_str.lower() for keyword in ["404", "not found", "error"]), \
                f"Error should be descriptive: {error_str}"
            
            logger.info(f"✅ Error format is consistent: {error_str}")