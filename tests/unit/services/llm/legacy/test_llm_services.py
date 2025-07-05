"""
Tests for the LLM service implementations.

NOTE: These are legacy tests. Current tests are distributed across
test_mock_service.py, test_openai_service.py, and test_factory.py
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from doc_ai_helper_backend.models.llm import LLMResponse, LLMUsage
from doc_ai_helper_backend.services.llm.mock_service import MockLLMService
from doc_ai_helper_backend.services.llm.factory import LLMServiceFactory
from doc_ai_helper_backend.core.exceptions import ServiceNotFoundError

# Skip all tests in this file as they are legacy
pytestmark = pytest.mark.skip(
    reason="Legacy tests - functionality moved to dedicated test files"
)


# This allows running async tests
@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


class TestMockLLMService:
    """Tests for the MockLLMService."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock LLM service instance."""
        return MockLLMService(response_delay=0.1)

    @pytest.mark.asyncio
    async def test_query(self, mock_service):
        """Test basic query functionality."""
        response = await mock_service.query("hello")

        assert isinstance(response, LLMResponse)
        assert isinstance(response.content, str)
        assert len(response.content) > 0
        assert response.model == "mock-model"
        assert response.provider == "mock"
        assert isinstance(response.usage, LLMUsage)
        assert response.usage.prompt_tokens > 0

    @pytest.mark.asyncio
    async def test_capabilities(self, mock_service):
        """Test getting capabilities."""
        capabilities = await mock_service.get_capabilities()

        assert "mock-model" in capabilities.available_models
        assert "mock-model" in capabilities.max_tokens
        assert isinstance(capabilities.max_tokens["mock-model"], int)

    @pytest.mark.asyncio
    async def test_format_prompt(self, mock_service):
        """Test prompt formatting."""
        with patch(
            "doc_ai_helper_backend.services.llm.utils.templating.PromptTemplateManager.format_template"
        ) as mock_format:
            mock_format.return_value = "Formatted prompt"

            result = await mock_service.format_prompt("test", {"var": "value"})

            assert result == "Formatted prompt"
            mock_format.assert_called_once()

    @pytest.mark.asyncio
    async def test_token_estimation(self, mock_service):
        """Test token estimation."""
        text = "This is a test string for token estimation."
        token_count = await mock_service.estimate_tokens(text)

        assert token_count > 0
        # Basic check: ~4 characters per token
        assert token_count == len(text) // 4


class TestLLMServiceFactory:
    """Tests for the LLMServiceFactory."""

    def test_register_and_create(self):
        """Test registering and creating services."""
        # Register a test service if not already registered
        if "mock" not in LLMServiceFactory.get_available_providers():
            LLMServiceFactory.register("mock", MockLLMService)

        service = LLMServiceFactory.create("mock")
        assert isinstance(service, MockLLMService)

    def test_create_nonexistent(self):
        """Test creating a non-existent service."""
        with pytest.raises(ServiceNotFoundError):
            LLMServiceFactory.create("nonexistent")

    def test_get_available_providers(self):
        """Test getting available providers."""
        # Register a test service if not already registered
        if "mock" not in LLMServiceFactory.get_available_providers():
            LLMServiceFactory.register("mock", MockLLMService)

        providers = LLMServiceFactory.get_available_providers()
        assert "mock" in providers
