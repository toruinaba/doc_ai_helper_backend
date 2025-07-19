"""
Integration tests for GitHub-specific functionality.
These tests use actual GitHub services and should be run in integration test environment.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from doc_ai_helper_backend.api.endpoints.llm import router
from doc_ai_helper_backend.models.llm import (
    LLMQueryRequest,
    MessageItem,
    MessageRole,
    LLMResponse,
    LLMUsage,
    FunctionCall,
    ToolCall,
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
def mock_llm_service_with_github():
    """Create a mock LLM service with GitHub Function Calling support."""
    mock_service = AsyncMock()

    # Mock capabilities
    mock_service.get_capabilities.return_value = {
        "max_tokens": 4000,
        "supports_streaming": True,
        "supports_function_calling": True,
        "available_models": ["test-model"],
    }

    return mock_service


@pytest.mark.integration
class TestGitHubLLMIntegration:
    """Integration test class for GitHub-specific LLM functionality."""

    @patch('doc_ai_helper_backend.api.endpoints.llm.LLMServiceFactory.create_with_mcp')
    def test_github_issue_creation_request(
        self, mock_factory, test_app, mock_llm_service_with_github
    ):
        """Test GitHub issue creation through LLM API."""
        # Configure the factory mock to return our mock service
        mock_factory.return_value = mock_llm_service_with_github
        
        # Set up specific response for this test
        github_issue_response = LLMResponse(
            content="I'll create a GitHub issue for you with the provided details.",
            model="test-model",
            provider="test-provider",
            usage=LLMUsage(prompt_tokens=15, completion_tokens=25, total_tokens=40),
            tool_calls=[
                ToolCall(
                    id="call_123",
                    type="function",
                    function=FunctionCall(
                        name="create_git_issue",
                        arguments='{"repository": "test/repo", "title": "Test Issue", "description": "This is a test issue", "labels": ["bug"]}',
                    ),
                )
            ],
        )
        mock_llm_service_with_github.query.return_value = github_issue_response

        client = TestClient(test_app)

        # Request payload for GitHub issue creation
        request_data = {
            "prompt": "Please create a GitHub issue in the test/repo repository with the title 'Test Issue' and description 'This is a test issue'. Add the 'bug' label.",
            "model": "test-model",
            "options": {"functions": ["create_git_issue"]},
        }

        # Make request
        response = client.post("/query", json=request_data)

        # Assertions
        assert response.status_code == 200
        response_data = response.json()

        assert (
            response_data["content"]
            == "I'll create a GitHub issue for you with the provided details."
        )
        assert response_data["model"] == "test-model"
        assert response_data["provider"] == "test-provider"
        assert "tool_calls" in response_data
        assert len(response_data["tool_calls"]) == 1

        tool_call = response_data["tool_calls"][0]
        assert tool_call["function"]["name"] == "create_git_issue"

        # Parse and verify function arguments
        arguments = json.loads(tool_call["function"]["arguments"])
        assert arguments["repository"] == "test/repo"
        assert arguments["title"] == "Test Issue"
        assert arguments["description"] == "This is a test issue"
        assert arguments["labels"] == ["bug"]

        # Verify service was called correctly
        mock_llm_service_with_github.query.assert_called_once()
        
        # Verify factory was called
        mock_factory.assert_called_once()

    # Note: Additional GitHub-specific integration tests can be added here
    # These should test actual GitHub API integration when appropriate