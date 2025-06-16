"""
Test for LLM services in isolation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from doc_ai_helper_backend.services.llm import MockLLMService
from doc_ai_helper_backend.models.llm import LLMResponse, LLMUsage


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def mock_llm_service():
    """Return a mock LLM service instance."""
    return MockLLMService()


@pytest.mark.asyncio
async def test_mock_llm_query(mock_llm_service):
    """Test the mock LLM query method."""
    # Arrange
    prompt = "Test prompt"
    options = {"model": "test-model"}

    # Mock the query method to return a specific response
    mock_response = LLMResponse(
        content="This is a test response",
        model="test-model",
        provider="mock",
        usage=LLMUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        raw_response={"id": "test-123"},
    )

    mock_llm_service.query = AsyncMock(return_value=mock_response)

    # Act
    result = await mock_llm_service.query(prompt, options)

    # Assert
    assert result == mock_response
    assert result.content == "This is a test response"
    assert result.model == "test-model"
    assert result.provider == "mock"

    # Verify the mock was called with the right arguments
    mock_llm_service.query.assert_called_once_with(prompt, options)
