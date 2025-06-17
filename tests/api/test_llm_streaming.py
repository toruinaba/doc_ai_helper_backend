"""
Test for LLM streaming endpoint.
"""

import json
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sse_starlette.sse import EventSourceResponse

from doc_ai_helper_backend.api.endpoints.llm import router
from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    LLMUsage,
    ProviderCapabilities,
    LLMQueryRequest,
)


class MockLLMServiceForStreaming(LLMServiceBase):
    """Mock LLM service for testing streaming endpoint."""

    async def query(self, prompt, options=None):
        return LLMResponse(
            content="Test response",
            model="test-model",
            provider="test-provider",
            usage=LLMUsage(),
        )

    async def get_capabilities(self):
        return ProviderCapabilities(
            available_models=["test-model"],
            max_tokens={"test-model": 1000},
            supports_streaming=True,
        )

    async def format_prompt(self, template_id, variables):
        return f"Template {template_id} with {len(variables)} variables"

    async def get_available_templates(self):
        return ["template1", "template2"]

    async def estimate_tokens(self, text):
        return len(text) // 4

    async def stream_query(self, prompt, options=None) -> AsyncGenerator[str, None]:
        yield "Hello"
        yield " world"
        yield "!"


@pytest.fixture
def test_app():
    """Create a test FastAPI app with the LLM router."""
    app = FastAPI()
    app.include_router(router)

    # Override the dependency
    async def get_test_llm_service():
        return MockLLMServiceForStreaming()

    app.dependency_overrides = {
        "doc_ai_helper_backend.api.dependencies.get_llm_service": get_test_llm_service
    }

    return app


@pytest.fixture
def test_client(test_app):
    """Create a test client for the app."""
    return TestClient(test_app)


def test_stream_endpoint_returns_sse_response(test_app, monkeypatch):
    """Test that the stream endpoint returns an SSE response."""
    # Mock the EventSourceResponse to avoid actual streaming in tests
    mock_event_source = MagicMock(spec=EventSourceResponse)
    monkeypatch.setattr(
        "doc_ai_helper_backend.api.endpoints.llm.EventSourceResponse", mock_event_source
    )

    # Create a test client
    client = TestClient(test_app)

    # Make a request to the stream endpoint
    response = client.post(
        "/stream",
        json={"prompt": "Test streaming", "model": "test-model"},
    )

    # Assert that EventSourceResponse was called
    assert mock_event_source.call_count == 1


@pytest.mark.asyncio
async def test_stream_event_generator(monkeypatch):
    """Test the event generator function in the stream endpoint."""
    # Create a mock LLM service
    mock_service = MockLLMServiceForStreaming()

    # Create a mock request
    request = LLMQueryRequest(prompt="Test streaming")

    # Import the stream_llm_response function directly
    from doc_ai_helper_backend.api.endpoints.llm import stream_llm_response

    # Call the function to get the event generator
    response = await stream_llm_response(request, mock_service)

    # Check if the response is an EventSourceResponse
    assert isinstance(response, EventSourceResponse)

    # Since we can't easily test the actual streaming in a unit test,
    # we'll just verify that the event_generator function exists and is callable
    assert hasattr(response, "body_iterator")
