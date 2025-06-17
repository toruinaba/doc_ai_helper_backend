"""
Test for streaming support in LLM services.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

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
    """Return a mock LLM service instance with minimal response delay for faster tests."""
    return MockLLMService(response_delay=0.01)


@pytest.mark.asyncio
async def test_mock_llm_stream_query_produces_chunks(mock_llm_service):
    """Test that the mock LLM stream_query method produces chunks."""
    # Arrange
    prompt = "Test streaming response"

    # Act
    chunks = []
    async for chunk in mock_llm_service.stream_query(prompt):
        chunks.append(chunk)

    # Assert
    assert len(chunks) > 1  # Should produce multiple chunks
    assert "".join(chunks)  # Joined chunks should form a coherent response


@pytest.mark.asyncio
async def test_mock_llm_stream_query_with_options(mock_llm_service):
    """Test the mock LLM stream_query method with options."""
    # Arrange
    prompt = "Test streaming with options"
    options = {"model": "mock-model-large"}

    # Act
    chunks = []
    async for chunk in mock_llm_service.stream_query(prompt, options):
        chunks.append(chunk)

    # Assert
    assert len(chunks) > 1
    full_response = "".join(chunks)
    assert len(full_response) > 0
    # The response should contain the prompt length since our mock service
    # includes that in the response for longer prompts
    assert str(len(prompt)) in full_response


@pytest.mark.asyncio
async def test_mock_llm_capabilities_supports_streaming(mock_llm_service):
    """Test that the mock LLM service reports streaming capability."""
    # Act
    capabilities = await mock_llm_service.get_capabilities()

    # Assert
    assert capabilities.supports_streaming is True
