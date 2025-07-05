"""
Unit tests for LLM service common functionality.

This module contains tests for the LLMServiceCommon class that provides
shared logic for all LLM service implementations using composition pattern.

NOTE: These are legacy tests kept for reference. Current tests are in test_common.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, Optional, List

from doc_ai_helper_backend.services.llm.common import LLMServiceCommon
from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    MessageItem,
    MessageRole,
    FunctionDefinition,
    ToolChoice,
    LLMUsage,
)
from doc_ai_helper_backend.models.repository_context import (
    RepositoryContext,
    DocumentMetadata,
    DocumentType,
    GitService,
)

# Skip all tests in this file as they are legacy
pytestmark = pytest.mark.skip(
    reason="Legacy tests - functionality moved to composition-based implementation in test_common.py"
)


class MockProvider:
    """Mock LLM provider for testing LLMServiceCommon."""

    def __init__(self):
        self.prepare_options_calls = []
        self.api_calls = []
        self.response_conversions = []

    async def _prepare_provider_options(self, prompt: str, **kwargs) -> Dict[str, Any]:
        call_info = {"prompt": prompt, **kwargs}
        self.prepare_options_calls.append(call_info)
        return {
            "messages": [{"role": "user", "content": prompt}],
            "model": kwargs.get("options", {}).get("model", "default-model"),
        }

    async def _call_provider_api(self, options: Dict[str, Any]) -> Any:
        self.api_calls.append(options)
        return {
            "choices": [{"message": {"content": "Mock response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

    async def _stream_provider_api(self, options: Dict[str, Any]):
        self.api_calls.append(options)
        chunks = ["Mock ", "streaming ", "response"]
        for chunk in chunks:
            yield chunk

    async def _convert_provider_response(
        self, raw_response: Any, options: Dict[str, Any]
    ) -> LLMResponse:
        conversion_info = {"raw_response": raw_response, "options": options}
        self.response_conversions.append(conversion_info)
        return LLMResponse(
            content="Mock response",
            provider="mock",
            model=options.get("model", "default-model"),
            usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )


class TestLLMServiceCommon:
    """Test the LLM service common functionality."""

    @pytest.fixture
    def mock_provider(self):
        return MockProvider()

    @pytest.fixture
    def common_service(self):
        return LLMServiceCommon()

    @pytest.fixture
    def sample_repository_context(self):
        return RepositoryContext(
            repository="test/repo",
            owner="test",
            service=GitService.GITHUB,
            ref="main",
            documents=[
                DocumentMetadata(
                    path="README.md",
                    name="README.md",
                    type=DocumentType.MARKDOWN,
                    size=1024,
                )
            ],
        )

    @pytest.fixture
    def sample_document_metadata(self):
        return DocumentMetadata(
            path="test.md", name="test.md", type=DocumentType.MARKDOWN, size=512
        )

    @pytest.mark.asyncio
    async def test_basic_query(self, common_service, mock_provider):
        """Test basic query functionality."""
        prompt = "Test prompt"

        response = await common_service.query(prompt)

        assert isinstance(response, LLMResponse)
        assert response.content == "Mock response"
        assert response.provider == "mock"

        # Verify provider methods were called
        assert len(mock_provider.prepare_options_calls) == 1
        assert len(mock_provider.api_calls) == 1
        assert len(mock_provider.response_conversions) == 1

    @pytest.mark.asyncio
    async def test_query_with_conversation_history(self, common_service, mock_provider):
        """Test query with conversation history."""
        prompt = "Follow-up question"
        history = [
            MessageItem(role=MessageRole.USER, content="Initial question"),
            MessageItem(role=MessageRole.ASSISTANT, content="Initial response"),
        ]

        response = await common_service.query(prompt, conversation_history=history)

        assert isinstance(response, LLMResponse)

        # Check that conversation history was passed to provider
        prepare_call = mock_provider.prepare_options_calls[0]
        assert prepare_call["conversation_history"] == history

    @pytest.mark.asyncio
    async def test_query_with_options(self, common_service, mock_provider):
        """Test query with custom options."""
        prompt = "Test prompt"
        options = {"model": "custom-model", "temperature": 0.7}

        response = await common_service.query(prompt, options=options)

        assert isinstance(response, LLMResponse)

        # Check that options were passed to provider
        prepare_call = mock_provider.prepare_options_calls[0]
        assert prepare_call["options"] == options

    @pytest.mark.asyncio
    async def test_query_with_repository_context(
        self, common_service, mock_provider, sample_repository_context
    ):
        """Test query with repository context."""
        prompt = "Analyze this repository"

        with patch.object(
            common_service,
            "_build_system_prompt",
            return_value="System prompt with context",
        ):
            response = await common_service.query(
                prompt, repository_context=sample_repository_context
            )

        assert isinstance(response, LLMResponse)

        # Verify system prompt was generated
        common_service._build_system_prompt.assert_called_once()

    @pytest.mark.asyncio
    async def test_stream_query(self, common_service, mock_provider):
        """Test streaming query functionality."""
        prompt = "Test streaming prompt"

        chunks = []
        async for chunk in common_service.stream_query(prompt):
            chunks.append(chunk)

        assert chunks == ["Mock ", "streaming ", "response"]

        # Verify provider methods were called
        assert len(mock_provider.prepare_options_calls) == 1
        assert len(mock_provider.api_calls) == 1

    @pytest.mark.asyncio
    async def test_query_with_tools(self, common_service, mock_provider):
        """Test query with function calling tools."""
        prompt = "Use tools to help"
        tools = [
            FunctionDefinition(
                name="test_tool",
                description="A test tool",
                parameters={
                    "type": "object",
                    "properties": {"input": {"type": "string"}},
                    "required": ["input"],
                },
            )
        ]

        response = await common_service.query_with_tools(prompt, tools)

        assert isinstance(response, LLMResponse)

        # Check that tools were passed to provider
        prepare_call = mock_provider.prepare_options_calls[0]
        assert prepare_call["tools"] == tools

    @pytest.mark.asyncio
    async def test_query_with_tools_and_choice(self, common_service, mock_provider):
        """Test query with tools and tool choice."""
        prompt = "Use specific tool"
        tools = [
            FunctionDefinition(
                name="specific_tool",
                description="A specific tool",
                parameters={"type": "object", "properties": {}},
            )
        ]
        tool_choice = ToolChoice.FUNCTION

        response = await common_service.query_with_tools(
            prompt, tools, tool_choice=tool_choice
        )

        assert isinstance(response, LLMResponse)

        # Check that tool choice was passed to provider
        prepare_call = mock_provider.prepare_options_calls[0]
        assert prepare_call["tool_choice"] == tool_choice

    @pytest.mark.asyncio
    async def test_caching_functionality(self, common_service, mock_provider):
        """Test that caching works correctly."""
        prompt = "Same prompt"

        # First call
        response1 = await common_service.query(prompt)

        # Second call with same prompt (should be cached)
        response2 = await common_service.query(prompt)

        assert response1.content == response2.content

        # Provider should only be called once due to caching
        # Note: This depends on caching implementation in LLMServiceCommon
        # The test might need adjustment based on actual caching behavior

    @pytest.mark.asyncio
    async def test_system_prompt_generation(
        self, common_service, sample_repository_context, sample_document_metadata
    ):
        """Test system prompt generation with context."""
        with patch.object(common_service, "_build_system_prompt") as mock_build:
            mock_build.return_value = "Generated system prompt"

            await common_service.query(
                "Test prompt",
                repository_context=sample_repository_context,
                document_metadata=sample_document_metadata,
                document_content="Test document content",
            )

            mock_build.assert_called_once()
            call_args = mock_build.call_args[1]  # Get keyword arguments
            assert call_args["repository_context"] == sample_repository_context
            assert call_args["document_metadata"] == sample_document_metadata
            assert call_args["document_content"] == "Test document content"

    def test_build_system_prompt_basic(self, common_service):
        """Test basic system prompt building."""
        with patch(
            "doc_ai_helper_backend.services.llm.utils.PromptTemplateManager"
        ) as mock_template_manager:
            mock_template_manager.return_value.format_template.return_value = (
                "Formatted prompt"
            )

            result = common_service._build_system_prompt()

            assert result == "Formatted prompt"
            mock_template_manager.return_value.format_template.assert_called_once()

    def test_build_system_prompt_with_context(
        self, common_service, sample_repository_context
    ):
        """Test system prompt building with repository context."""
        with patch(
            "doc_ai_helper_backend.services.llm.utils.PromptTemplateManager"
        ) as mock_template_manager:
            mock_template_manager.return_value.format_template.return_value = (
                "Context-aware prompt"
            )

            result = common_service._build_system_prompt(
                repository_context=sample_repository_context,
                template_id="contextual_document_assistant_ja",
            )

            assert result == "Context-aware prompt"

            # Check that template was called with context variables
            call_args = mock_template_manager.return_value.format_template.call_args
            template_vars = call_args[0][1]  # Second argument (variables)
            assert "repository" in template_vars

    @pytest.mark.asyncio
    async def test_error_handling(self, common_service, mock_provider):
        """Test error handling in common service."""
        # Mock provider to raise an exception
        mock_provider._call_provider_api = AsyncMock(side_effect=Exception("API Error"))

        with pytest.raises(Exception) as exc_info:
            await common_service.query("Test prompt")

        assert "API Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_function_execution(self, common_service):
        """Test function execution capability."""
        from doc_ai_helper_backend.models.llm import FunctionCall

        # Mock function registry
        mock_function = MagicMock(return_value={"result": "success"})
        available_functions = {"test_function": mock_function}

        function_call = FunctionCall(name="test_function", arguments={"param": "value"})

        result = await common_service.execute_function_call(
            function_call, available_functions
        )

        assert result == {"result": "success"}
        mock_function.assert_called_once_with(param="value")

    @pytest.mark.asyncio
    async def test_get_available_functions(self, common_service):
        """Test getting available functions."""
        with patch(
            "doc_ai_helper_backend.services.llm.utils.FunctionRegistry"
        ) as mock_registry:
            mock_registry.return_value.get_all_functions.return_value = [
                FunctionDefinition(
                    name="func1", description="Function 1", parameters={}
                ),
                FunctionDefinition(
                    name="func2", description="Function 2", parameters={}
                ),
            ]

            functions = await common_service.get_available_functions()

            assert len(functions) == 2
            assert functions[0].name == "func1"
            assert functions[1].name == "func2"

    @pytest.mark.asyncio
    async def test_format_prompt(self, common_service):
        """Test prompt formatting."""
        with patch(
            "doc_ai_helper_backend.services.llm.utils.PromptTemplateManager"
        ) as mock_template_manager:
            mock_template_manager.return_value.format_template.return_value = (
                "Formatted template"
            )

            result = await common_service.format_prompt(
                "test_template", {"variable": "value"}
            )

            assert result == "Formatted template"
            mock_template_manager.return_value.format_template.assert_called_once_with(
                "test_template", {"variable": "value"}
            )

    @pytest.mark.asyncio
    async def test_get_available_templates(self, common_service):
        """Test getting available templates."""
        with patch(
            "doc_ai_helper_backend.services.llm.utils.PromptTemplateManager"
        ) as mock_template_manager:
            mock_template_manager.return_value.get_available_templates.return_value = [
                "template1",
                "template2",
                "template3",
            ]

            templates = await common_service.get_available_templates()

            assert templates == ["template1", "template2", "template3"]
            mock_template_manager.return_value.get_available_templates.assert_called_once()
