"""Tests for GitHub Function Calling integration."""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from doc_ai_helper_backend.services.llm.openai_service import OpenAIService
from doc_ai_helper_backend.services.llm.mock_service import MockLLMService
from doc_ai_helper_backend.services.llm.github_functions import (
    get_github_function_definitions,
    register_github_functions,
    create_github_function_registry,
)
from doc_ai_helper_backend.models.llm import FunctionDefinition, ToolCall, FunctionCall


class TestGitHubFunctionCalling:
    """Test cases for GitHub Function Calling integration."""

    def test_get_github_function_definitions(self):
        """Test getting GitHub function definitions."""
        func_defs = get_github_function_definitions()

        assert len(func_defs) == 3
        assert isinstance(func_defs[0], FunctionDefinition)

        # Check function names
        func_names = [func.name for func in func_defs]
        assert "create_git_issue" in func_names
        assert "create_git_pull_request" in func_names
        assert "check_git_repository_permissions" in func_names

    def test_create_github_function_registry(self):
        """Test creating a function registry with GitHub functions."""
        registry = create_github_function_registry()

        # Check that functions are registered
        assert "create_git_issue" in registry._functions
        assert "create_git_pull_request" in registry._functions
        assert "check_git_repository_permissions" in registry._functions

        # Check function definitions
        func_defs = registry.get_all_function_definitions()
        assert len(func_defs) == 3

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"GITHUB_TOKEN": "mock_token"})
    async def test_mock_service_github_function_calling(self):
        """Test GitHub function calling with MockLLMService."""
        service = MockLLMService()

        # Get GitHub function definitions
        github_functions = get_github_function_definitions()

        # Test issue creation prompt
        response = await service.query(
            prompt="Create an issue for this bug I found",
            options={"functions": github_functions},
        )

        assert response.content == "I'll help you with that GitHub operation."
        assert response.tool_calls is not None
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].function.name == "create_git_issue"

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"GITHUB_TOKEN": "mock_token"})
    async def test_mock_service_github_pr_function_calling(self):
        """Test GitHub PR function calling with MockLLMService."""
        service = MockLLMService()

        # Get GitHub function definitions
        github_functions = get_github_function_definitions()

        # Test PR creation prompt (using keywords that trigger GitHub function)
        response = await service.query(
            prompt="Create pull request for my changes",
            options={"functions": github_functions},
        )

        assert response.content == "I'll help you with that GitHub operation."
        assert response.tool_calls is not None
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].function.name == "create_git_pull_request"

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"GITHUB_TOKEN": "mock_token"})
    async def test_mock_service_github_permissions_function_calling(self):
        """Test GitHub permissions function calling with MockLLMService."""
        service = MockLLMService()

        # Get GitHub function definitions
        github_functions = get_github_function_definitions()

        # Test permissions check prompt (using keywords that trigger GitHub function)
        response = await service.query(
            prompt="Check repository permissions for this repo",
            options={"functions": github_functions},
        )

        assert response.content == "I'll help you with that GitHub operation."
        assert response.tool_calls is not None
        assert len(response.tool_calls) == 1
        assert (
            response.tool_calls[0].function.name == "check_git_repository_permissions"
        )

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"GITHUB_TOKEN": "mock_token"})
    async def test_mock_service_normal_query_no_functions(self):
        """Test normal query without function calling."""
        service = MockLLMService()

        # Get GitHub function definitions
        github_functions = get_github_function_definitions()

        # Test normal prompt that shouldn't trigger function calling
        response = await service.query(
            prompt="What is the weather like today?",
            options={"functions": github_functions},
        )

        # Should be a question response since the prompt contains "?"
        assert "That's an interesting question" in response.content
        assert response.tool_calls is None or len(response.tool_calls) == 0

    @pytest.mark.asyncio
    @patch("doc_ai_helper_backend.services.llm.openai_service.AsyncOpenAI")
    @patch.dict("os.environ", {"GITHUB_TOKEN": "mock_token"})
    async def test_openai_service_github_function_calling_preparation(
        self, mock_openai_class
    ):
        """Test OpenAI service prepares GitHub function calling correctly."""
        # Setup mock OpenAI client
        mock_client = AsyncMock()
        mock_openai_class.return_value = mock_client

        # Mock OpenAI response without tool calls
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "I'll help you create an issue."
        mock_response.choices[0].message.tool_calls = None
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 70
        mock_response.model_dump.return_value = {"test": "response"}

        mock_client.chat.completions.create.return_value = mock_response

        service = OpenAIService(api_key="test_key")

        # Get GitHub function definitions
        github_functions = get_github_function_definitions()

        # Test with GitHub functions
        response = await service.query(
            prompt="Create an issue for this bug",
            options={"functions": github_functions},
        )

        # Verify that the API was called with tools
        call_args = mock_client.chat.completions.create.call_args
        assert "tools" in call_args.kwargs
        assert len(call_args.kwargs["tools"]) == 3

        # Check tool format
        tools = call_args.kwargs["tools"]
        tool_names = [tool["function"]["name"] for tool in tools]
        assert "create_git_issue" in tool_names

    @pytest.mark.asyncio
    @patch("doc_ai_helper_backend.services.llm.openai_service.AsyncOpenAI")
    @patch.dict("os.environ", {"GITHUB_TOKEN": "mock_token"})
    async def test_openai_service_github_tool_calls_response(self, mock_openai_class):
        """Test OpenAI service handles GitHub tool calls in response."""
        # Setup mock OpenAI client
        mock_client = AsyncMock()
        mock_openai_class.return_value = mock_client

        # Mock OpenAI response with tool calls
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.type = "function"
        mock_tool_call.function.name = "create_git_issue"
        mock_tool_call.function.arguments = (
            '{"repository": "test/repo", "title": "Test Issue"}'
        )

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_response.choices[0].message.tool_calls = [mock_tool_call]
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 70
        mock_response.model_dump.return_value = {"test": "response"}

        mock_client.chat.completions.create.return_value = mock_response

        service = OpenAIService(api_key="test_key")

        # Get GitHub function definitions
        github_functions = get_github_function_definitions()

        # Test with GitHub functions
        response = await service.query(
            prompt="Create an issue for this bug",
            options={"functions": github_functions},
        )

        # Verify tool calls are properly parsed
        assert response.tool_calls is not None
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].id == "call_123"
        assert response.tool_calls[0].function.name == "create_git_issue"

        # Parse arguments to verify they're valid JSON
        args = json.loads(response.tool_calls[0].function.arguments)
        assert args["repository"] == "test/repo"
        assert args["title"] == "Test Issue"

    def test_function_definition_structure(self):
        """Test that GitHub function definitions have correct structure."""
        func_defs = get_github_function_definitions()

        for func_def in func_defs:
            # Check required fields
            assert hasattr(func_def, "name")
            assert hasattr(func_def, "description")
            assert hasattr(func_def, "parameters")

            # Check parameters structure
            params = func_def.parameters
            assert "type" in params
            assert params["type"] == "object"
            assert "properties" in params
            assert "required" in params

            # Check that required parameters are in properties
            for required_param in params["required"]:
                assert required_param in params["properties"]
