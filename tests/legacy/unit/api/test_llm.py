"""
Test for LLM API endpoints.

This module tests the LLM API endpoints using a mock LLM service.
"""

import pytest


def test_query_llm_endpoint(client):
    """Test the /query endpoint with a mock LLM service."""
    # Make the request with mock provider
    request_data = {
        "prompt": "Test prompt",
        "provider": "mock",
        "model": "mock-model",
        "options": {"temperature": 0.7},
    }

    response = client.post("/api/v1/llm/query", json=request_data)

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert data["provider"] == "mock"
    assert "model" in data


def test_get_capabilities_endpoint(client):
    """Test the /capabilities endpoint with a mock LLM service."""
    # Make the request
    response = client.get("/api/v1/llm/capabilities")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "available_models" in data
    assert "supports_function_calling" in data
    assert "supports_vision" in data


def test_list_templates_endpoint(client):
    """Test the /templates endpoint with a mock LLM service."""
    # Make the request
    response = client.get("/api/v1/llm/templates")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_format_prompt_endpoint(client):
    """Test the /format-prompt endpoint with a mock LLM service."""
    # Make the request
    template_id = "document_qa"
    variables = {"document": "Sample document", "question": "Sample question"}

    response = client.post(
        f"/api/v1/llm/format-prompt?template_id={template_id}", json=variables
    )

    # Verify response
    assert response.status_code == 200
    assert isinstance(response.text, str)


def test_query_llm_endpoint_error(client):
    """Test error handling in the /query endpoint."""
    # Make the request with error simulation prompt
    request_data = {
        "prompt": "simulate_error",  # Mock serviceでエラーを発生させるキーワード
        "provider": "mock",
        "model": "mock-model",
    }

    response = client.post("/api/v1/llm/query", json=request_data)

    # Verify response
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
