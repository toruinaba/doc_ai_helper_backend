"""
Unit tests for LLM API endpoints with GitHub Function Calling integration.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from doc_ai_helper_backend.api.endpoints.llm import router
from doc_ai_helper_backend.api.dependencies import get_llm_service
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


class TestLLMGitHubIntegration:
    """Test class for LLM API endpoints with GitHub Function Calling."""

    def test_github_issue_creation_request(
        self, test_app, mock_llm_service_with_github
    ):
        """Test GitHub issue creation through LLM API."""
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

        # Override the dependency
        def override_get_llm_service():
            return mock_llm_service_with_github

        test_app.dependency_overrides[get_llm_service] = override_get_llm_service

        try:
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
        finally:
            # Clean up
            test_app.dependency_overrides.clear()

    def test_github_pr_creation_request(self, test_app, mock_llm_service_with_github):
        """Test GitHub pull request creation through LLM API."""
        # Set up specific response for this test
        github_pr_response = LLMResponse(
            content="I'll create a GitHub pull request for you with the provided changes.",
            model="test-model",
            provider="test-provider",
            usage=LLMUsage(prompt_tokens=20, completion_tokens=30, total_tokens=50),
            tool_calls=[
                ToolCall(
                    id="call_456",
                    type="function",
                    function=FunctionCall(
                        name="create_git_pull_request",
                        arguments='{"repository": "test/repo", "title": "Test PR", "description": "This is a test PR", "head_branch": "feature/test", "base_branch": "main"}',
                    ),
                )
            ],
        )
        mock_llm_service_with_github.query.return_value = github_pr_response

        # Override the dependency
        def override_get_llm_service():
            return mock_llm_service_with_github

        test_app.dependency_overrides[get_llm_service] = override_get_llm_service

        try:
            client = TestClient(test_app)

            # Request payload for GitHub PR creation
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
                == "I'll create a GitHub pull request for you with the provided changes."
            )
            assert response_data["model"] == "test-model"
            assert "tool_calls" in response_data
            assert len(response_data["tool_calls"]) == 1

            tool_call = response_data["tool_calls"][0]
            assert tool_call["function"]["name"] == "create_git_pull_request"

            # Parse and verify function arguments
            arguments = json.loads(tool_call["function"]["arguments"])
            assert arguments["repository"] == "test/repo"
            assert arguments["title"] == "Test PR"
            assert arguments["description"] == "This is a test PR"
            assert arguments["head_branch"] == "feature/test"
            assert arguments["base_branch"] == "main"

            # Verify LLM service was called
            mock_llm_service_with_github.query.assert_called_once()
        finally:
            # Clean up
            test_app.dependency_overrides.clear()

    def test_normal_query_without_github_functions(
        self, test_app, mock_llm_service_with_github
    ):
        """Test normal query without GitHub function calls."""
        # Set up specific response for this test
        normal_response = LLMResponse(
            content="This is a normal response without function calls.",
            model="test-model",
            provider="test-provider",
            usage=LLMUsage(prompt_tokens=10, completion_tokens=15, total_tokens=25),
        )
        mock_llm_service_with_github.query.return_value = normal_response

        # Override the dependency
        def override_get_llm_service():
            return mock_llm_service_with_github

        test_app.dependency_overrides[get_llm_service] = override_get_llm_service

        try:
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
            assert (
                "tool_calls" not in response_data or response_data["tool_calls"] is None
            )

            # Verify LLM service was called
            mock_llm_service_with_github.query.assert_called_once()
        finally:
            # Clean up
            test_app.dependency_overrides.clear()

    def test_github_functions_with_conversation_history(
        self, test_app, mock_llm_service_with_github
    ):
        """Test GitHub function calling with conversation history."""
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

        # Override the dependency
        def override_get_llm_service():
            return mock_llm_service_with_github

        test_app.dependency_overrides[get_llm_service] = override_get_llm_service

        try:
            client = TestClient(test_app)

            # Request payload with conversation history
            request_data = {
                "prompt": "Based on our previous discussion, please create a GitHub issue for this bug.",
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

            assert (
                response_data["content"]
                == "I'll create a GitHub issue for you with the provided details."
            )
            assert "tool_calls" in response_data

            # Verify service was called with conversation history
            mock_llm_service_with_github.query.assert_called_once()
            call_args = mock_llm_service_with_github.query.call_args
            assert call_args.kwargs.get("conversation_history") is not None
            assert len(call_args.kwargs["conversation_history"]) == 3
        finally:
            # Clean up
            test_app.dependency_overrides.clear()

    def test_github_function_with_invalid_repository_format(
        self, test_app, mock_llm_service_with_github
    ):
        """Test GitHub function with invalid repository format handling."""

        # Setup - modify mock to handle invalid repository
        def invalid_repo_side_effect(*args, **kwargs):
            return LLMResponse(
                content="I detected an invalid repository format. Please provide repository in 'owner/repo' format.",
                model="test-model",
                provider="test-provider",
                usage=LLMUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
                tool_calls=[
                    ToolCall(
                        id="call_error",
                        type="function",
                        function=FunctionCall(
                            name="create_git_issue",
                            arguments='{"repository": "invalid-repo", "title": "Test", "description": "Test"}',
                        ),
                    )
                ],
            )

        mock_llm_service_with_github.query.side_effect = invalid_repo_side_effect

        # Override the dependency
        def override_get_llm_service():
            return mock_llm_service_with_github

        test_app.dependency_overrides[get_llm_service] = override_get_llm_service

        try:
            client = TestClient(test_app)

            # Request with invalid repository format
            request_data = {
                "prompt": "Create an issue in invalid-repo",
                "model": "test-model",
                "options": {"functions": ["create_git_issue"]},
            }

            # Make request
            response = client.post("/query", json=request_data)

            # Assertions
            assert response.status_code == 200
            response_data = response.json()

            assert "tool_calls" in response_data
            tool_call = response_data["tool_calls"][0]
            arguments = json.loads(tool_call["function"]["arguments"])
            assert (
                arguments["repository"] == "invalid-repo"
            )  # LLM attempted to use invalid format
        finally:
            # Clean up
            test_app.dependency_overrides.clear()

