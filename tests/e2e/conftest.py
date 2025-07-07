"""
Pytest configuration and fixtures for E2E tests.

This configuration file provides common fixtures and setup for user story-based E2E tests.
"""

import asyncio
import pytest
import logging
from pathlib import Path
from typing import AsyncGenerator

from .helpers.api_client import BackendAPIClient
from .helpers.forgejo_client import ForgejoVerificationClient
from .helpers.test_data import E2ETestData
from .helpers import (
    ScenarioRunner,
    PerformanceMonitor,
    DataValidator,
    TestDataGenerator,
    FrontendSimulator,
)

# Configure logging for E2E tests
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def validate_environment():
    """Validate that the environment is properly configured for E2E tests."""
    is_valid, messages = E2ETestData.validate_environment_with_fallback()

    if not is_valid:
        pytest.skip(f"Environment validation failed: {'; '.join(messages)}")

    # Log warnings but continue
    for message in messages:
        if "warning" in message.lower() or "demo" in message.lower():
            logger.warning(message)
        else:
            logger.info(message)

    logger.info("Environment validation passed")


@pytest.fixture(scope="session")
def fixtures_path() -> Path:
    """Get the path to E2E test fixtures."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def scenario_runner(fixtures_path: Path) -> ScenarioRunner:
    """Create a scenario runner for E2E tests."""
    return ScenarioRunner(fixtures_path)


@pytest.fixture
def performance_monitor() -> PerformanceMonitor:
    """Create a performance monitor for E2E tests."""
    return PerformanceMonitor()


@pytest.fixture
def data_validator(fixtures_path: Path) -> DataValidator:
    """Create a data validator with schemas for E2E tests."""
    schemas_path = fixtures_path / "schemas"
    return DataValidator(schemas_path if schemas_path.exists() else None)


@pytest.fixture
def test_data_generator() -> TestDataGenerator:
    """Create a test data generator for E2E tests."""
    return TestDataGenerator(seed=42)  # Fixed seed for reproducible tests


@pytest.fixture(scope="session")
async def backend_api_client(
    validate_environment,
) -> AsyncGenerator[BackendAPIClient, None]:
    """
    Create a backend API client for the test session.

    This fixture ensures the backend server is running and accessible.
    """
    async with BackendAPIClient(base_url=E2ETestData.BACKEND_API_URL) as client:
        # Wait for the backend server to be available
        if not await client.wait_for_server(max_attempts=10, delay=2.0):
            pytest.skip("Backend API server is not available")

        logger.info(f"Backend API client connected to {E2ETestData.BACKEND_API_URL}")
        yield client


@pytest.fixture(scope="session")
async def forgejo_client(
    validate_environment,
) -> AsyncGenerator[ForgejoVerificationClient, None]:
    """
    Create a Forgejo verification client for the test session.
    """
    config = E2ETestData.get_forgejo_config()

    # Check if this is a demo/example configuration
    is_demo_config = (
        config.base_url == "https://git.example.com"
        or config.owner == "test-owner"
        or config.repo == "test-repo"
    )

    if is_demo_config:
        pytest.skip(
            "Skipping Forgejo tests - demo/example configuration detected. "
            "Set real FORGEJO_BASE_URL, TEST_FORGEJO_OWNER, and TEST_FORGEJO_REPO to run tests."
        )

    async with ForgejoVerificationClient(
        base_url=config.base_url,
        token=config.token,
        username=config.username,
        password=config.password,
        verify_ssl=config.verify_ssl,
    ) as client:
        # Check Forgejo connectivity
        if not await client.check_connection():
            pytest.skip(f"Forgejo instance at {config.base_url} is not accessible")

        # Verify test repository exists
        repo_info = await client.get_repository_info(config.owner, config.repo)
        if not repo_info:
            pytest.skip(f"Test repository {config.owner}/{config.repo} does not exist")

        logger.info(f"Forgejo client connected to {config.base_url}")
        yield client


@pytest.fixture(scope="function")
async def clean_test_issues(forgejo_client: ForgejoVerificationClient):
    """
    Clean up test issues before and after each test.
    """
    config = E2ETestData.get_forgejo_config()

    # Clean up before test
    await forgejo_client.cleanup_test_issues(
        config.owner, config.repo, E2ETestData.TEST_ISSUE_MARKER
    )

    yield

    # Clean up after test
    await forgejo_client.cleanup_test_issues(
        config.owner, config.repo, E2ETestData.TEST_ISSUE_MARKER
    )


@pytest.fixture(scope="function")
def test_config():
    """Provide test configuration for individual tests."""
    return E2ETestData.get_forgejo_config()


@pytest.fixture(scope="function")
def test_data():
    """Provide test data utilities for individual tests."""
    return E2ETestData


@pytest.mark.asyncio
@pytest.fixture(scope="function")
async def sample_document(backend_api_client: BackendAPIClient, test_config):
    """
    Fetch a sample document for testing.

    This fixture provides a document that can be used in tests
    without needing to fetch it repeatedly.
    """
    try:
        document = await backend_api_client.get_document(
            service="forgejo",
            owner=test_config.owner,
            repo=test_config.repo,
            path="README.md",
        )
        return document
    except Exception as e:
        pytest.skip(f"Could not fetch sample document: {e}")


# Pytest marks for different test categories
def pytest_configure(config):
    """Configure pytest with custom marks."""
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "forgejo: marks tests that require Forgejo")
    config.addinivalue_line(
        "markers", "llm: marks tests that require LLM functionality"
    )
    config.addinivalue_line("markers", "mcp: marks tests that require MCP tools")


def pytest_collection_modifyitems(config, items):
    """Modify test items during collection."""
    # Add 'e2e' marker to all tests in the e2e directory
    for item in items:
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)


# Skip E2E tests by default unless explicitly requested
def pytest_runtest_setup(item):
    """Set up individual test runs."""
    if item.get_closest_marker("e2e"):
        if not item.config.getoption("--run-e2e", default=False):
            pytest.skip("E2E tests skipped (use --run-e2e to run)")


def pytest_addoption(parser):
    """Add command line options for E2E tests."""
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run E2E tests (requires backend server and Forgejo instance)",
    )
