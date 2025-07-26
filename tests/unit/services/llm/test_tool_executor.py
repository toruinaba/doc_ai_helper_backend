"""
Test cases for tool execution and followup functionality.

ツール実行とフォローアップ機能のテストケース群。
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from doc_ai_helper_backend.services.llm.tool_executor import (
    handle_tool_execution_and_followup,
    convert_repository_context_to_dict,
    generate_followup_response,
    build_tool_results_summary,
)
from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    LLMUsage,
    ToolCall,
    FunctionCall,
    FunctionDefinition,
    MessageItem,
    MessageRole,
)
from doc_ai_helper_backend.models.repository_context import (
    RepositoryContext,
    GitService,
)


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing."""
    service = AsyncMock()
    service.execute_function_call = AsyncMock()
    service._prepare_provider_options = AsyncMock()
    service._call_provider_api = AsyncMock()
    service._convert_provider_response = AsyncMock()
    return service


@pytest.fixture
def sample_repository_context():
    """Sample repository context for testing."""
    return RepositoryContext(
        service=GitService.GITHUB,
        owner="test-owner",
        repo="test-repo",
        ref="main",
        current_path="docs/README.md",
        base_url="https://api.github.com"
    )


@pytest.fixture
def sample_tool_call():
    """Sample tool call for testing."""
    return ToolCall(
        id="call_123",
        function=FunctionCall(
            name="test_tool",
            arguments='{"param1": "value1"}'
        )
    )


@pytest.fixture
def sample_llm_response_with_tools(sample_tool_call):
    """Sample LLM response with tool calls."""
    return LLMResponse(
        content="I'll execute the tool for you.",
        model="test-model",
        provider="test-provider",
        usage=LLMUsage(prompt_tokens=50, completion_tokens=25, total_tokens=75),
        tool_calls=[sample_tool_call]
    )


@pytest.fixture
def sample_function_definitions():
    """Sample function definitions for testing."""
    return [
        FunctionDefinition(
            name="test_tool",
            description="A test tool for testing",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "Test parameter"}
                },
                "required": ["param1"]
            }
        )
    ]


class TestHandleToolExecutionAndFollowup:
    """Test tool execution and followup handling."""

    async def test_successful_tool_execution_and_followup(
        self,
        mock_llm_service,
        sample_llm_response_with_tools,
        sample_function_definitions,
        sample_repository_context
    ):
        """Test successful tool execution and followup response generation."""
        # Setup
        tool_execution_result = {"success": True, "result": "Tool executed successfully"}
        mock_llm_service.execute_function_call.return_value = tool_execution_result
        
        followup_response = LLMResponse(
            content="Based on the tool execution, here's the complete answer.",
            model="test-model",
            provider="test-provider",
            usage=LLMUsage(prompt_tokens=30, completion_tokens=40, total_tokens=70)
        )
        mock_llm_service._convert_provider_response.return_value = followup_response
        
        original_prompt = "Please analyze this document"
        conversation_history = [
            MessageItem(role=MessageRole.USER, content="Hello")
        ]
        system_prompt = "You are a helpful assistant"
        options = {"temperature": 0.5}
        
        # Execute
        await handle_tool_execution_and_followup(
            service=mock_llm_service,
            llm_response=sample_llm_response_with_tools,
            tools=sample_function_definitions,
            repository_context=sample_repository_context,
            original_prompt=original_prompt,
            conversation_history=conversation_history,
            system_prompt=system_prompt,
            options=options
        )
        
        # Assert
        assert sample_llm_response_with_tools.tool_execution_results is not None
        assert len(sample_llm_response_with_tools.tool_execution_results) == 1
        
        result = sample_llm_response_with_tools.tool_execution_results[0]
        assert result["tool_call_id"] == "call_123"
        assert result["function_name"] == "test_tool"
        assert result["result"] == tool_execution_result
        assert "error" not in result
        
        # Check that content was updated with followup response
        assert sample_llm_response_with_tools.content == "Based on the tool execution, here's the complete answer."
        
        # Check that usage was updated
        assert sample_llm_response_with_tools.usage.prompt_tokens == 80  # 50 + 30
        assert sample_llm_response_with_tools.usage.completion_tokens == 65  # 25 + 40
        assert sample_llm_response_with_tools.usage.total_tokens == 145  # 75 + 70

    async def test_tool_execution_failure(
        self,
        mock_llm_service,
        sample_llm_response_with_tools,
        sample_function_definitions,
        sample_repository_context
    ):
        """Test tool execution failure handling."""
        # Setup
        mock_llm_service.execute_function_call.side_effect = Exception("Tool execution failed")
        
        followup_response = LLMResponse(
            content="There was an error executing the tool.",
            model="test-model",
            provider="test-provider",
            usage=LLMUsage(prompt_tokens=20, completion_tokens=15, total_tokens=35)
        )
        mock_llm_service._convert_provider_response.return_value = followup_response
        
        # Execute
        await handle_tool_execution_and_followup(
            service=mock_llm_service,
            llm_response=sample_llm_response_with_tools,
            tools=sample_function_definitions,
            repository_context=sample_repository_context,
            original_prompt="Test prompt",
            conversation_history=None,
            system_prompt=None,
            options=None
        )
        
        # Assert
        assert sample_llm_response_with_tools.tool_execution_results is not None
        assert len(sample_llm_response_with_tools.tool_execution_results) == 1
        
        result = sample_llm_response_with_tools.tool_execution_results[0]
        assert result["tool_call_id"] == "call_123"
        assert result["function_name"] == "test_tool"
        assert result["error"] == "Tool execution failed"
        assert "result" not in result

    async def test_multiple_tool_execution(
        self,
        mock_llm_service,
        sample_function_definitions
    ):
        """Test execution of multiple tools."""
        # Setup
        tool_calls = [
            ToolCall(
                id="call_1",
                function=FunctionCall(name="test_tool", arguments='{"param1": "value1"}')
            ),
            ToolCall(
                id="call_2", 
                function=FunctionCall(name="test_tool", arguments='{"param1": "value2"}')
            )
        ]
        
        llm_response = LLMResponse(
            content="I'll execute multiple tools.",
            model="test-model",
            provider="test-provider",
            usage=LLMUsage(prompt_tokens=60, completion_tokens=30, total_tokens=90),
            tool_calls=tool_calls
        )
        
        mock_llm_service.execute_function_call.side_effect = [
            {"success": True, "result": "Result 1"},
            {"success": True, "result": "Result 2"}
        ]
        
        followup_response = LLMResponse(
            content="Both tools executed successfully.",
            model="test-model",
            provider="test-provider",
            usage=LLMUsage(prompt_tokens=25, completion_tokens=20, total_tokens=45)
        )
        mock_llm_service._convert_provider_response.return_value = followup_response
        
        # Execute
        await handle_tool_execution_and_followup(
            service=mock_llm_service,
            llm_response=llm_response,
            tools=sample_function_definitions,
            repository_context=None,
            original_prompt="Execute multiple tools",
            conversation_history=None,
            system_prompt=None,
            options=None
        )
        
        # Assert
        assert len(llm_response.tool_execution_results) == 2
        assert llm_response.tool_execution_results[0]["tool_call_id"] == "call_1"
        assert llm_response.tool_execution_results[1]["tool_call_id"] == "call_2"
        assert mock_llm_service.execute_function_call.call_count == 2

    async def test_followup_response_failure(
        self,
        mock_llm_service,
        sample_llm_response_with_tools,
        sample_function_definitions
    ):
        """Test followup response generation failure."""
        # Setup
        mock_llm_service.execute_function_call.return_value = {"success": True}
        mock_llm_service._convert_provider_response.return_value = None  # Followup fails
        
        original_content = sample_llm_response_with_tools.content
        
        # Execute
        await handle_tool_execution_and_followup(
            service=mock_llm_service,
            llm_response=sample_llm_response_with_tools,
            tools=sample_function_definitions,
            repository_context=None,
            original_prompt="Test prompt",
            conversation_history=None,
            system_prompt=None,
            options=None
        )
        
        # Assert
        # Content should remain unchanged when followup fails
        assert sample_llm_response_with_tools.content == original_content
        assert sample_llm_response_with_tools.tool_execution_results is not None


class TestConvertRepositoryContextToDict:
    """Test repository context conversion."""

    def test_convert_repository_context_to_dict_success(self, sample_repository_context):
        """Test successful repository context conversion."""
        # Execute
        result = convert_repository_context_to_dict(sample_repository_context)
        
        # Assert
        assert result is not None
        assert result["service"] == "github"
        assert result["owner"] == "test-owner"
        assert result["repo"] == "test-repo"
        assert result["ref"] == "main"
        assert result["current_path"] == "docs/README.md"
        assert result["base_url"] == "https://api.github.com"

    def test_convert_repository_context_to_dict_none(self):
        """Test repository context conversion with None input."""
        # Execute
        result = convert_repository_context_to_dict(None)
        
        # Assert
        assert result is None

    def test_convert_repository_context_to_dict_enum_handling(self):
        """Test repository context conversion with enum values."""
        # Setup
        repo_context = RepositoryContext(
            service=GitService.FORGEJO,  # Enum value
            owner="test-owner",
            repo="test-repo",
            ref="main",
            current_path=None,
            base_url="https://forgejo.example.com"
        )
        
        # Execute
        result = convert_repository_context_to_dict(repo_context)
        
        # Assert
        assert result is not None
        assert result["service"] == "forgejo"
        assert result["current_path"] is None


class TestGenerateFollowupResponse:
    """Test followup response generation."""

    async def test_generate_followup_response_success(self, mock_llm_service):
        """Test successful followup response generation."""
        # Setup
        tool_calls = [
            ToolCall(
                id="call_1",
                function=FunctionCall(name="summarize_document", arguments='{}')
            )
        ]
        
        tool_results = [
            {
                "tool_call_id": "call_1",
                "function_name": "summarize_document",
                "result": {"success": True, "result": '{"summary": "Document summary"}'}
            }
        ]
        
        conversation_history = [
            MessageItem(role=MessageRole.USER, content="Previous message")
        ]
        
        expected_response = LLMResponse(
            content="Here's the complete analysis based on the tool results.",
            model="test-model",
            provider="test-provider",
            usage=LLMUsage(prompt_tokens=40, completion_tokens=30, total_tokens=70)
        )
        
        mock_llm_service._prepare_provider_options.return_value = {"mock": "options"}
        mock_llm_service._call_provider_api.return_value = {"mock": "response"}
        mock_llm_service._convert_provider_response.return_value = expected_response
        
        # Execute
        result = await generate_followup_response(
            service=mock_llm_service,
            original_prompt="Analyze this document",
            tool_calls=tool_calls,
            tool_results=tool_results,
            conversation_history=conversation_history,
            system_prompt="You are helpful",
            options={"temperature": 0.5}
        )
        
        # Assert
        assert result is not None
        assert result.content == "Here's the complete analysis based on the tool results."
        
        # Verify that service methods were called
        mock_llm_service._prepare_provider_options.assert_called_once()
        mock_llm_service._call_provider_api.assert_called_once()
        mock_llm_service._convert_provider_response.assert_called_once()

    async def test_generate_followup_response_exception(self, mock_llm_service):
        """Test followup response generation with exception."""
        # Setup
        mock_llm_service._prepare_provider_options.side_effect = Exception("API error")
        
        # Execute
        result = await generate_followup_response(
            service=mock_llm_service,
            original_prompt="Test prompt",
            tool_calls=[],
            tool_results=[],
            conversation_history=None,
            system_prompt=None,
            options=None
        )
        
        # Assert
        assert result is None

    async def test_generate_followup_response_builds_correct_history(self, mock_llm_service):
        """Test that followup response builds correct conversation history."""
        # Setup
        tool_calls = [
            ToolCall(
                id="call_1",
                function=FunctionCall(name="test_tool", arguments='{}')
            )
        ]
        
        tool_results = [
            {
                "tool_call_id": "call_1",
                "function_name": "test_tool",
                "result": {"success": True}
            }
        ]
        
        original_history = [
            MessageItem(role=MessageRole.USER, content="First message"),
            MessageItem(role=MessageRole.ASSISTANT, content="First response")
        ]
        
        mock_response = LLMResponse(
            content="Followup response",
            model="test-model",
            provider="test-provider",
            usage=LLMUsage(prompt_tokens=20, completion_tokens=15, total_tokens=35)
        )
        
        mock_llm_service._prepare_provider_options.return_value = {"mock": "options"}
        mock_llm_service._call_provider_api.return_value = {"mock": "response"}
        mock_llm_service._convert_provider_response.return_value = mock_response
        
        # Execute
        await generate_followup_response(
            service=mock_llm_service,
            original_prompt="Analyze document",
            tool_calls=tool_calls,
            tool_results=tool_results,
            conversation_history=original_history,
            system_prompt="System prompt",
            options={"temperature": 0.7}
        )
        
        # Assert
        # Check that _prepare_provider_options was called with correct parameters
        call_args = mock_llm_service._prepare_provider_options.call_args
        assert call_args is not None
        
        # The conversation history passed should include original history + new messages
        passed_history = call_args[1]["conversation_history"]
        assert len(passed_history) >= len(original_history)
        
        # Check that tools are set to None to prevent recursion
        assert call_args[1]["tools"] is None
        assert call_args[1]["tool_choice"] is None


class TestBuildToolResultsSummary:
    """Test tool results summary building."""

    def test_build_tool_results_summary_success_cases(self):
        """Test building summary for successful tool results."""
        tool_results = [
            {
                "function_name": "summarize_document",
                "result": {
                    "success": True,
                    "result": '{"summary": "Document summary"}'
                }
            },
            {
                "function_name": "create_recommendations",
                "result": {
                    "success": True,
                    "result": '{"recommendations": ["Improve A", "Fix B"]}'
                }
            },
            {
                "function_name": "analyze_code",
                "result": {
                    "success": True,
                    "result": '{"analysis": "Code analysis results"}'
                }
            }
        ]
        
        # Execute
        result = build_tool_results_summary(tool_results)
        
        # Assert
        assert len(result) == 3
        assert "✅ summarize_document: 要約が生成されました" in result
        assert "✅ create_recommendations: 改善提案が生成されました" in result
        assert "✅ analyze_code: 分析が完了しました" in result

    def test_build_tool_results_summary_error_cases(self):
        """Test building summary for error cases."""
        tool_results = [
            {
                "function_name": "failed_tool",
                "error": "Tool execution failed"
            },
            {
                "function_name": "another_failed_tool",
                "result": {
                    "success": False,
                    "error": "Internal tool error"
                }
            }
        ]
        
        # Execute
        result = build_tool_results_summary(tool_results)
        
        # Assert
        assert len(result) == 2
        assert "❌ failed_tool: エラーが発生しました - Tool execution failed" in result
        assert "❌ another_failed_tool: Internal tool error" in result

    def test_build_tool_results_summary_mixed_cases(self):
        """Test building summary for mixed success and error cases."""
        tool_results = [
            {
                "function_name": "success_tool",
                "result": {"success": True, "result": "Simple result"}
            },
            {
                "function_name": "error_tool",
                "error": "Failed to execute"
            },
            {
                "function_name": "complex_tool",
                "result": {"success": True}  # No specific result content
            }
        ]
        
        # Execute
        result = build_tool_results_summary(tool_results)
        
        # Assert
        assert len(result) == 3
        assert "✅ success_tool: 結果を取得しました" in result
        assert "❌ error_tool: エラーが発生しました - Failed to execute" in result
        assert "✅ complex_tool: 実行完了" in result

    def test_build_tool_results_summary_invalid_json(self):
        """Test building summary with invalid JSON in results."""
        tool_results = [
            {
                "function_name": "invalid_json_tool",
                "result": {
                    "success": True,
                    "result": "Invalid JSON string: {not json}"
                }
            }
        ]
        
        # Execute
        result = build_tool_results_summary(tool_results)
        
        # Assert
        assert len(result) == 1
        assert "✅ invalid_json_tool: 結果を取得しました" in result

    def test_build_tool_results_summary_unknown_tool(self):
        """Test building summary for tools without function name."""
        tool_results = [
            {
                "result": {"success": True}
                # Missing function_name
            }
        ]
        
        # Execute
        result = build_tool_results_summary(tool_results)
        
        # Assert
        assert len(result) == 1
        assert "✅ 不明なツール: 実行完了" in result

    def test_build_tool_results_summary_non_dict_result(self):
        """Test building summary with non-dictionary result."""
        tool_results = [
            {
                "function_name": "string_result_tool",
                "result": "Simple string result"
            }
        ]
        
        # Execute
        result = build_tool_results_summary(tool_results)
        
        # Assert
        assert len(result) == 1
        assert "✅ string_result_tool: 実行完了" in result