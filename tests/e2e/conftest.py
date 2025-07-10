"""
E2E test configuration and fixtures.

This module provides specialized fixtures and configuration for end-to-end tests,
including API clients, test data, and environment setup.
"""

import os
import sys
import pytest
import asyncio
import logging
from typing import AsyncGenerator

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from tests.e2e.helpers.config import E2EConfig
from tests.e2e.helpers.api_client import BackendAPIClient
from tests.e2e.helpers.git_verification import GitVerificationClient

logger = logging.getLogger(__name__)


# Configure asyncio event loop policy for testing
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


@pytest.fixture(scope="session")
def e2e_config():
    """E2E test configuration fixture."""
    return E2EConfig()


@pytest.fixture(scope="function")
async def backend_api_client(e2e_config: E2EConfig) -> AsyncGenerator[BackendAPIClient, None]:
    """Async backend API client fixture."""
    async with BackendAPIClient(base_url=e2e_config.api_base_url) as client:
        # Wait for server to be available
        if not await client.wait_for_server(max_attempts=30, delay=1.0):
            pytest.skip("Backend server is not available")
        yield client


@pytest.fixture(scope="function")
async def git_verification_client(e2e_config: E2EConfig) -> AsyncGenerator[GitVerificationClient, None]:
    """Git verification client fixture."""
    async with GitVerificationClient(config=e2e_config) as client:
        yield client


@pytest.fixture(scope="function")
async def clean_test_issues(git_verification_client: GitVerificationClient, e2e_config: E2EConfig):
    """Fixture to clean up test issues before and after tests."""
    # Pre-test cleanup
    if e2e_config.github_repo:
        await git_verification_client.cleanup_test_issues(
            service="github",
            owner=e2e_config.github_owner,
            repo=e2e_config.github_repo,
            title_pattern="E2E-TEST"
        )
    
    if e2e_config.forgejo_repo:
        await git_verification_client.cleanup_test_issues(
            service="forgejo",
            owner=e2e_config.forgejo_owner,
            repo=e2e_config.forgejo_repo,
            title_pattern="E2E-TEST"
        )
    
    yield
    
    # Post-test cleanup
    if e2e_config.github_repo:
        await git_verification_client.cleanup_test_issues(
            service="github",
            owner=e2e_config.github_owner,
            repo=e2e_config.github_repo,
            title_pattern="E2E-TEST"
        )
    
    if e2e_config.forgejo_repo:
        await git_verification_client.cleanup_test_issues(
            service="forgejo",
            owner=e2e_config.forgejo_owner,
            repo=e2e_config.forgejo_repo,
            title_pattern="E2E-TEST"
        )


@pytest.fixture(scope="function")
def test_repository_context(e2e_config: E2EConfig):
    """Provide repository context for tests."""
    return {
        "github": {
            "service": "github",
            "owner": e2e_config.github_owner,
            "repo": e2e_config.github_repo,
            "available": bool(e2e_config.github_repo)
        },
        "forgejo": {
            "service": "forgejo",
            "owner": e2e_config.forgejo_owner,
            "repo": e2e_config.forgejo_repo,
            "available": bool(e2e_config.forgejo_repo)
        }
    }


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "mcp: MCP integration tests")
    config.addinivalue_line("markers", "github: GitHub service tests")
    config.addinivalue_line("markers", "forgejo: Forgejo service tests")
    config.addinivalue_line("markers", "slow: Slow running tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test paths."""
    for item in items:
        # Add e2e marker to all tests in e2e directory
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Add service-specific markers
        if "github" in str(item.fspath) or "github" in item.name:
            item.add_marker(pytest.mark.github)
        
        if "forgejo" in str(item.fspath) or "forgejo" in item.name:
            item.add_marker(pytest.mark.forgejo)
        
        # Add MCP marker for issue workflow tests
        if "mcp" in str(item.fspath) or "issue" in item.name:
            item.add_marker(pytest.mark.mcp)


def pytest_runtest_setup(item):
    """Setup function called before each test."""
    # Skip tests that require unavailable services
    if item.get_closest_marker("github"):
        config = E2EConfig()
        if not config.github_repo:
            pytest.skip("GitHub repository not configured for E2E tests")
    
    if item.get_closest_marker("forgejo"):
        config = E2EConfig()
        if not config.forgejo_repo:
            pytest.skip("Forgejo repository not configured for E2E tests")