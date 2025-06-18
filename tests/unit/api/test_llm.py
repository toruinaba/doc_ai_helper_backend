"""
Test for LLM API endpoints.

This module tests the LLM API endpoints using a mock LLM service.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from doc_ai_helper_backend.main import app
from doc_ai_helper_backend.services.llm.mock_service import MockLLMService
from doc_ai_helper_backend.models.llm import LLMResponse, LLMUsage
from doc_ai_helper_backend.core.config import settings
from doc_ai_helper_backend.api.dependencies import get_llm_service


# Override settings for testing
settings.environment = "testing"
settings.default_llm_provider = "mock"


# Create a test mock service
mock_service = MockLLMService(response_delay=0)


# Override the dependency
def get_test_llm_service():
    """Return a mock LLM service for testing."""
    return mock_service


app.dependency_overrides[get_llm_service] = get_test_llm_service


@pytest.fixture
def client():
    """Return a test client for the API."""
    return TestClient(app)


@pytest.fixture
def setup_mock_service():
    """Setup and return the mock service with reset methods."""
    # Reset the mock service before each test
    global mock_service

    # Save original methods
    original_query = mock_service.query
    original_get_capabilities = mock_service.get_capabilities
    original_get_available_templates = mock_service.get_available_templates
    original_format_prompt = mock_service.format_prompt

    yield mock_service

    # Restore original methods after test
    mock_service.query = original_query
    mock_service.get_capabilities = original_get_capabilities
    mock_service.get_available_templates = original_get_available_templates
    mock_service.format_prompt = original_format_prompt


def test_query_llm_endpoint(client, setup_mock_service):
    """Test the /query endpoint with a mock LLM service."""
    # Setup the mock service query method
    mock_response = LLMResponse(
        content="This is a test response from the mock LLM service.",
        model="mock-model",
        provider="mock",
        usage=LLMUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        raw_response={"id": "mock-123"},
    )

    setup_mock_service.query = AsyncMock(return_value=mock_response)

    # Make the request
    request_data = {
        "prompt": "Test prompt",
        "model": "mock-model",
        "options": {"temperature": 0.7},
    }

    response = client.post("/api/v1/llm/query", json=request_data)

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "This is a test response from the mock LLM service."
    assert data["model"] == "mock-model"
    assert data["provider"] == "mock"
    assert data["usage"]["prompt_tokens"] == 10
    assert data["usage"]["completion_tokens"] == 20
    assert data["usage"]["total_tokens"] == 30


def test_get_capabilities_endpoint(client, setup_mock_service):
    """Test the /capabilities endpoint with a mock LLM service."""
    # Setup the mock service capabilities method
    mock_capabilities = {
        "provider": "mock",
        "available_models": ["mock-model", "mock-model-large"],
        "max_tokens": {"mock-model": 4096, "mock-model-large": 8192},
        "supports_streaming": False,
        "supports_function_calling": True,
        "supports_vision": False,
    }

    setup_mock_service.get_capabilities = AsyncMock(return_value=mock_capabilities)

    # Make the request
    response = client.get("/api/v1/llm/capabilities")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "available_models" in data
    assert "mock-model" in data["available_models"]
    assert "max_tokens" in data
    assert data["max_tokens"]["mock-model"] == 4096
    assert data["supports_function_calling"] == True
    assert data["supports_vision"] == False


def test_list_templates_endpoint(client, setup_mock_service):
    """Test the /templates endpoint with a mock LLM service."""
    # Setup the mock service templates method
    mock_templates = ["document_qa", "document_summary"]

    setup_mock_service.get_available_templates = AsyncMock(return_value=mock_templates)

    # Make the request
    response = client.get("/api/v1/llm/templates")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "document_qa" in data
    assert "document_summary" in data


def test_format_prompt_endpoint(client, setup_mock_service):
    """Test the /format-prompt endpoint with a mock LLM service."""
    # Setup the mock service format_prompt method
    formatted_prompt = "Formatted prompt with variables"

    setup_mock_service.format_prompt = AsyncMock(return_value=formatted_prompt)

    # Make the request
    template_id = "document_qa"
    variables = {"document": "Sample document", "question": "Sample question"}

    response = client.post(
        f"/api/v1/llm/format-prompt?template_id={template_id}", json=variables
    )

    # Verify response
    assert response.status_code == 200
    assert response.text.strip('"') == formatted_prompt


def test_query_llm_endpoint_error(client, setup_mock_service):
    """Test error handling in the /query endpoint."""
    # Setup the mock service to raise an exception
    error_message = "Test error message"
    setup_mock_service.query = AsyncMock(side_effect=Exception(error_message))

    # Make the request
    request_data = {"prompt": "Test prompt that causes an error", "model": "mock-model"}

    response = client.post("/api/v1/llm/query", json=request_data)

    # Verify response
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert error_message in data["detail"]
