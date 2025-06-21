"""
Unit tests for LLM API endpoints with conversation history support.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sse_starlette.sse import EventSourceResponse

from doc_ai_helper_backend.api.endpoints.llm import router
from doc_ai_helper_backend.models.llm import (
    LLMQueryRequest,
    MessageItem,
    MessageRole,
    LLMResponse,
    LLMUsage,
    ProviderCapabilities,
)


@pytest.fixture
def test_app():
    """Create a test FastAPI app with the LLM router."""
    from doc_ai_helper_backend.api.error_handlers import setup_error_handlers

    app = FastAPI()
    app.include_router(router)

    # Set up error handlers for proper error handling in tests
    setup_error_handlers(app)

    return app


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service for testing."""
    mock_service = AsyncMock()

    # Mock query method
    mock_service.query.return_value = LLMResponse(
        content="Mock response with conversation history",
        model="test-model",
        provider="test-provider",
        usage=LLMUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
    )

    # Mock capabilities
    mock_service.get_capabilities.return_value = ProviderCapabilities(
        available_models=["test-model"],
        max_tokens={"test-model": 1000},
        supports_streaming=True,
    )

    return mock_service


@pytest.fixture
def test_client_with_mock(test_app, mock_llm_service):
    """Create a test client with mock LLM service."""
    from doc_ai_helper_backend.api.dependencies import get_llm_service

    # Override the dependency
    test_app.dependency_overrides[get_llm_service] = lambda: mock_llm_service

    client = TestClient(test_app)

    # Clean up after test
    yield client, mock_llm_service
    test_app.dependency_overrides.clear()


def test_query_endpoint_with_conversation_history(test_client_with_mock):
    """Test the query endpoint with conversation history."""
    client, mock_service = test_client_with_mock

    # Prepare request data with conversation history
    conversation_history = [
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi there! How can I help you?"},
    ]

    request_data = {
        "prompt": "What's the weather like?",
        "conversation_history": conversation_history,
        "model": "test-model",
        "options": {"temperature": 0.7},
    }

    # Send request
    response = client.post("/query", json=request_data)

    # Check response
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["content"] == "Mock response with conversation history"
    assert response_data["model"] == "test-model"

    # Verify that the service was called with conversation history
    mock_service.query.assert_called_once()
    call_args = mock_service.query.call_args

    # Check positional arguments
    assert call_args[0][0] == "What's the weather like?"  # prompt

    # Check keyword arguments
    assert "conversation_history" in call_args[1]
    assert "options" in call_args[1]

    # Verify conversation history was passed correctly
    passed_history = call_args[1]["conversation_history"]
    assert len(passed_history) == 2
    assert passed_history[0].role == "user"
    assert passed_history[0].content == "Hello!"
    assert passed_history[1].role == "assistant"
    assert passed_history[1].content == "Hi there! How can I help you?"

    # Verify options were passed correctly
    passed_options = call_args[1]["options"]
    assert passed_options["temperature"] == 0.7
    assert passed_options["model"] == "test-model"


def test_query_endpoint_without_conversation_history(test_client_with_mock):
    """Test the query endpoint without conversation history."""
    client, mock_service = test_client_with_mock

    request_data = {
        "prompt": "Hello, how are you?",
        "model": "test-model",
    }

    # Send request
    response = client.post("/query", json=request_data)

    # Check response
    assert response.status_code == 200

    # Verify that the service was called with None for conversation history
    mock_service.query.assert_called_once()
    call_args = mock_service.query.call_args

    assert call_args[0][0] == "Hello, how are you?"
    assert call_args[1]["conversation_history"] is None


def test_stream_endpoint_with_conversation_history(test_client_with_mock, monkeypatch):
    """Test the stream endpoint with conversation history."""
    client, mock_service = test_client_with_mock

    # Mock the EventSourceResponse to avoid actual streaming in tests
    mock_event_source = MagicMock(spec=EventSourceResponse)
    monkeypatch.setattr(
        "doc_ai_helper_backend.api.endpoints.llm.EventSourceResponse",
        mock_event_source,
    )

    # Prepare request data with conversation history
    conversation_history = [
        {"role": "user", "content": "Tell me a story"},
        {"role": "assistant", "content": "Once upon a time..."},
    ]

    request_data = {
        "prompt": "Continue the story",
        "conversation_history": conversation_history,
        "model": "test-model",
    }

    # Send request
    response = client.post("/stream", json=request_data)

    # Check that EventSourceResponse was created
    assert mock_event_source.call_count == 1

    # Verify that the service's stream_query was called with conversation history
    # Note: We can't easily verify the actual call since it's inside the event generator
    # But we can verify that the capabilities check was called
    mock_service.get_capabilities.assert_called_once()


@pytest.mark.asyncio
async def test_conversation_history_data_types():
    """Test that conversation history is properly converted to MessageItem objects."""
    from doc_ai_helper_backend.api.endpoints.llm import query_llm
    from doc_ai_helper_backend.services.llm.mock_service import MockLLMService

    # Create a real mock service to test data conversion
    mock_service = MockLLMService()

    # Create request with conversation history as dicts
    conversation_history_dicts = [
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi there!"},
    ]

    # Convert to MessageItem objects
    conversation_history = []
    for msg in conversation_history_dicts:
        role = MessageRole.USER if msg["role"] == "user" else MessageRole.ASSISTANT
        conversation_history.append(MessageItem(role=role, content=msg["content"]))

    request = LLMQueryRequest(
        prompt="How are you?",
        conversation_history=conversation_history,
    )

    # Call the endpoint function directly
    response = await query_llm(request, mock_service)

    # Check that the response is valid
    assert response.content
    assert (
        "conversation_history" in response.content.lower()
        or "会話履歴" in response.content
    )


@pytest.mark.asyncio
async def test_stream_endpoint_conversation_history_integration():
    """Test that stream endpoint properly handles conversation history."""
    from doc_ai_helper_backend.api.endpoints.llm import stream_llm_response
    from doc_ai_helper_backend.services.llm.mock_service import MockLLMService

    # Create a real mock service
    mock_service = MockLLMService()

    # Create request with conversation history
    conversation_history = [
        MessageItem(role=MessageRole.USER, content="Start a story"),
        MessageItem(role=MessageRole.ASSISTANT, content="Once upon a time..."),
    ]

    request = LLMQueryRequest(
        prompt="Continue the story",
        conversation_history=conversation_history,
    )

    # Call the endpoint function directly
    response = await stream_llm_response(request, mock_service)

    # Check that an EventSourceResponse was returned
    assert isinstance(response, EventSourceResponse)


def test_query_endpoint_error_handling(test_client_with_mock):
    """Test error handling in query endpoint."""
    client, mock_service = test_client_with_mock

    # Make the service raise an exception
    mock_service.query.side_effect = Exception("Test error")

    request_data = {
        "prompt": "Test prompt",
        "conversation_history": [{"role": "user", "content": "Hello"}],
    }

    # Send request
    response = client.post("/query", json=request_data)

    # Check that the error is handled properly
    assert response.status_code == 500
    response_data = response.json()

    # The error should contain the message and detail from LLMServiceException
    assert "message" in response_data
    assert "detail" in response_data
    assert "Error querying LLM" in response_data["message"]
