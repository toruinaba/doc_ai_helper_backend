"""
Unit tests for LLM API endpoints with Git service abstraction.
Tests the integration between LLM and Git services at the abstraction level,
using MockGitService to maintain proper architectural boundaries.
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
def mock_llm_service_with_git():
    """Create a mock LLM service with Git Function Calling support."""
    mock_service = AsyncMock()

    # Mock capabilities
    mock_service.get_capabilities.return_value = {
        "max_tokens": 4000,
        "supports_streaming": True,
        "supports_function_calling": True,
        "available_models": ["test-model"],
    }

    return mock_service


class TestLLMGitServiceAbstraction:
    """Test class for LLM API endpoints with Git service abstraction."""

    @patch('doc_ai_helper_backend.api.endpoints.llm.LLMServiceFactory.create_with_mcp')
    def test_git_issue_creation_abstraction(
        self, mock_factory, test_app, mock_llm_service_with_git
    ):
        """Test Git issue creation through LLM API using abstraction."""
        # Configure the factory mock to return our mock service
        mock_factory.return_value = mock_llm_service_with_git
        
        # Set up response for generic git issue creation
        git_issue_response = LLMResponse(
            content="I'll create a Git issue for you with the provided details.",
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
        mock_llm_service_with_git.query.return_value = git_issue_response

        client = TestClient(test_app)

        # Request payload for generic git issue creation
        request_data = {
            "prompt": "Please create a Git issue in the test/repo repository with the title 'Test Issue' and description 'This is a test issue'. Add the 'bug' label.",
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
            == "I'll create a Git issue for you with the provided details."
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
        mock_llm_service_with_git.query.assert_called_once()
        
        # Verify factory was called
        mock_factory.assert_called_once()

    @patch('doc_ai_helper_backend.api.endpoints.llm.LLMServiceFactory.create_with_mcp')
    def test_git_pr_creation_abstraction(
        self, mock_factory, test_app, mock_llm_service_with_git
    ):
        """Test Git pull request creation through LLM API using abstraction."""
        # Configure the factory mock to return our mock service
        mock_factory.return_value = mock_llm_service_with_git
        
        # Set up response for generic git PR creation
        git_pr_response = LLMResponse(
            content="I'll create a Git pull request for you with the provided changes.",
            model="test-model",
            provider="test-provider",
            usage=LLMUsage(prompt_tokens=20, completion_tokens=30, total_tokens=50),
            tool_calls=[
                ToolCall(
                    id="call_456",
                    type="function",
                    function=FunctionCall(
                        name="create_git_pull_request",
                        arguments='{"repository": "test/repo", "title": "Test PR", "description": "This is a test PR", "source_branch": "feature/test", "target_branch": "main"}',
                    ),
                )
            ],
        )
        mock_llm_service_with_git.query.return_value = git_pr_response

        client = TestClient(test_app)

        # Request payload for generic git PR creation
        request_data = {
            "prompt": "Please create a pull request in test/repo from feature/test to main with title 'Test PR' and description 'This is a test PR'.",
            "model": "test-model",
            "options": {"functions": ["create_git_pull_request"]},
        }

        # Make request
        response = client.post("/query", json=request_data)

        # Assertions
        assert response.status_code == 200
        response_data = response.json()

        assert (
            response_data["content"]
            == "I'll create a Git pull request for you with the provided changes."
        )
        assert response_data["model"] == "test-model"
        assert response_data["provider"] == "test-provider"
        assert "tool_calls" in response_data
        assert len(response_data["tool_calls"]) == 1

        tool_call = response_data["tool_calls"][0]
        assert tool_call["function"]["name"] == "create_git_pull_request"

        # Parse and verify function arguments
        arguments = json.loads(tool_call["function"]["arguments"])
        assert arguments["repository"] == "test/repo"
        assert arguments["title"] == "Test PR"
        assert arguments["description"] == "This is a test PR"
        assert arguments["source_branch"] == "feature/test"
        assert arguments["target_branch"] == "main"

        # Verify service was called correctly
        mock_llm_service_with_git.query.assert_called_once()
        
        # Verify factory was called
        mock_factory.assert_called_once()

    @patch('doc_ai_helper_backend.api.endpoints.llm.LLMServiceFactory.create_with_mcp')
    def test_normal_query_without_git_functions(
        self, mock_factory, test_app, mock_llm_service_with_git
    ):
        """Test normal query without Git function calls."""
        # Configure the factory mock to return our mock service
        mock_factory.return_value = mock_llm_service_with_git
        
        # Set up response for normal query
        normal_response = LLMResponse(
            content="This is a normal response without function calls.",
            model="test-model",
            provider="test-provider",
            usage=LLMUsage(prompt_tokens=10, completion_tokens=15, total_tokens=25),
        )
        mock_llm_service_with_git.query.return_value = normal_response

        client = TestClient(test_app)

        # Request payload for normal query
        request_data = {
            "prompt": "What is the capital of France?",
            "model": "test-model",
        }

        # Make request
        response = client.post("/query", json=request_data)

        # Assertions
        assert response.status_code == 200
        response_data = response.json()

        assert (
            response_data["content"]
            == "This is a normal response without function calls."
        )
        assert response_data["model"] == "test-model"
        assert response_data["provider"] == "test-provider"
        assert "tool_calls" not in response_data or response_data.get("tool_calls") is None

        # Verify service was called correctly
        mock_llm_service_with_git.query.assert_called_once()
        
        # Verify factory was called
        mock_factory.assert_called_once()

    @patch('doc_ai_helper_backend.api.endpoints.llm.LLMServiceFactory.create_with_mcp')
    def test_git_functions_with_conversation_history(
        self, mock_factory, test_app, mock_llm_service_with_git
    ):
        """Test Git function calling with conversation history."""
        # Configure the factory mock to return our mock service
        mock_factory.return_value = mock_llm_service_with_git
        
        # Set up response for git function with conversation
        git_issue_response = LLMResponse(
            content="Based on our discussion, I'll create a Git issue for this bug.",
            model="test-model",
            provider="test-provider",
            usage=LLMUsage(prompt_tokens=25, completion_tokens=35, total_tokens=60),
            tool_calls=[
                ToolCall(
                    id="call_789",
                    type="function",
                    function=FunctionCall(
                        name="create_git_issue",
                        arguments='{"repository": "test/repo", "title": "Authentication Bug", "description": "Users cannot log in with email addresses", "labels": ["bug", "authentication"]}',
                    ),
                )
            ],
        )
        mock_llm_service_with_git.query.return_value = git_issue_response

        client = TestClient(test_app)

        # Request payload with conversation history
        request_data = {
            "prompt": "Based on our previous discussion, please create a Git issue for this bug.",
            "model": "test-model",
            "conversation_history": [
                {
                    "role": "user",
                    "content": "I found a bug in the authentication system",
                },
                {
                    "role": "assistant",
                    "content": "Can you provide more details about the authentication bug?",
                },
                {
                    "role": "user",
                    "content": "Users can't log in with their email addresses",
                },
            ],
            "options": {"functions": ["create_git_issue"]},
        }

        # Make request
        response = client.post("/query", json=request_data)

        # Assertions
        assert response.status_code == 200
        response_data = response.json()

        assert "tool_calls" in response_data
        assert len(response_data["tool_calls"]) == 1

        tool_call = response_data["tool_calls"][0]
        assert tool_call["function"]["name"] == "create_git_issue"
        
        arguments = json.loads(tool_call["function"]["arguments"])
        assert arguments["repository"] == "test/repo"
        assert arguments["title"] == "Authentication Bug"
        assert "authentication" in arguments["labels"]

        # Verify service was called with conversation history
        mock_llm_service_with_git.query.assert_called_once()
        call_args = mock_llm_service_with_git.query.call_args
        assert call_args.kwargs.get("conversation_history") is not None
        assert len(call_args.kwargs["conversation_history"]) == 3
        
        # Verify factory was called
        mock_factory.assert_called_once()