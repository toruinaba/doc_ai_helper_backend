"""
Test for LLM service common functionality.

This module contains unit tests for the LLMServiceCommon class.
Note: LLMServiceCommon is a composition helper class used by actual LLM services.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from doc_ai_helper_backend.services.llm.common import LLMServiceCommon
from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    LLMUsage,
    MessageItem,
    MessageRole,
    FunctionDefinition,
    ProviderCapabilities,
)
from doc_ai_helper_backend.core.exceptions import LLMServiceException


class MockLLMService(LLMServiceBase):
    """Mock LLM service for testing common functionality."""

    def __init__(self):
        self.prepare_options_calls = []
        self.call_api_calls = []
        self.convert_response_calls = []
        self.stream_api_calls = []

    async def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_streaming=True,
            supports_function_calling=True,
            available_models=["mock-model"],
            max_context_length=8192,
        )

    async def estimate_tokens(self, text: str) -> int:
        return len(text.split())

    async def _prepare_provider_options(
        self,
        prompt: str,
        conversation_history=None,
        options=None,
        system_prompt=None,
        tools=None,
        tool_choice=None,
    ) -> Dict[str, Any]:
        call_info = {
            "prompt": prompt,
            "conversation_history": conversation_history,
            "options": options,
            "system_prompt": system_prompt,
            "tools": tools,
            "tool_choice": tool_choice,
        }
        self.prepare_options_calls.append(call_info)
        return {
            "model": "mock-model",
            "messages": [{"role": "user", "content": prompt}],
            **(options or {}),
        }

    async def _call_provider_api(self, provider_options: Dict[str, Any]) -> Any:
        self.call_api_calls.append(provider_options)
        return {
            "choices": [{"message": {"content": "Mock response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "model": "mock-model",
        }

    async def _convert_provider_response(
        self, raw_response: Any, provider_options: Dict[str, Any]
    ) -> LLMResponse:
        self.convert_response_calls.append((raw_response, provider_options))
        return LLMResponse(
            content="Mock response",
            model="mock-model",
            provider="mock",
            usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            raw_response=raw_response,
        )

    async def _stream_provider_api(self, provider_options: Dict[str, Any]):
        self.stream_api_calls.append(provider_options)
        for chunk in ["Mock ", "streaming ", "response"]:
            yield chunk


class TestLLMServiceCommon:
    """Test the LLM service common functionality."""

    @pytest.fixture
    def common_service(self):
        return LLMServiceCommon()

    @pytest.fixture
    def mock_service(self):
        return MockLLMService()

    @pytest.fixture
    def sample_message_history(self):
        return [
            MessageItem(role=MessageRole.USER, content="Previous question"),
            MessageItem(role=MessageRole.ASSISTANT, content="Previous answer"),
        ]

    @pytest.fixture
    def sample_tools(self):
        return [
            FunctionDefinition(
                name="test_function",
                description="A test function",
                parameters={
                    "type": "object",
                    "properties": {"param": {"type": "string"}},
                    "required": ["param"],
                },
            )
        ]

    def test_initialization(self, common_service):
        """Test that LLMServiceCommon initializes correctly."""
        assert common_service is not None
        assert hasattr(common_service, "template_manager")
        assert hasattr(common_service, "cache_service")
        assert hasattr(common_service, "system_prompt_builder")
        assert hasattr(common_service, "function_manager")

    def test_cache_key_generation(self, common_service):
        """Test cache key generation functionality."""
        # Test that cache key generation method exists and can be called
        assert hasattr(common_service, "_generate_cache_key")

        # Test basic cache key generation
        key = common_service._generate_cache_key(
            prompt="test prompt",
            conversation_history=None,
            options=None,
            repository_context=None,
            document_metadata=None,
            document_content=None,
            system_prompt_template="default",
        )
        assert isinstance(key, str)
        assert len(key) > 0

    def test_cache_key_consistency(self, common_service):
        """Test that same inputs generate same cache keys."""
        key1 = common_service._generate_cache_key(
            prompt="test prompt",
            conversation_history=None,
            options={"temperature": 0.7},
            repository_context=None,
            document_metadata=None,
            document_content=None,
            system_prompt_template="default",
        )

        key2 = common_service._generate_cache_key(
            prompt="test prompt",
            conversation_history=None,
            options={"temperature": 0.7},
            repository_context=None,
            document_metadata=None,
            document_content=None,
            system_prompt_template="default",
        )

        assert key1 == key2

    def test_cache_key_difference(self, common_service):
        """Test that different inputs generate different cache keys."""
        key1 = common_service._generate_cache_key(
            prompt="test prompt 1",
            conversation_history=None,
            options=None,
            repository_context=None,
            document_metadata=None,
            document_content=None,
            system_prompt_template="default",
        )

        key2 = common_service._generate_cache_key(
            prompt="test prompt 2",
            conversation_history=None,
            options=None,
            repository_context=None,
            document_metadata=None,
            document_content=None,
            system_prompt_template="default",
        )

        assert key1 != key2

    def test_common_service_composition(self, common_service):
        """Test that common service has expected composition components."""
        # Verify template manager
        from doc_ai_helper_backend.services.llm.utils.templating import (
            PromptTemplateManager,
        )

        assert isinstance(common_service.template_manager, PromptTemplateManager)

        # Verify cache service
        from doc_ai_helper_backend.services.llm.utils.caching import LLMCacheService

        assert isinstance(common_service.cache_service, LLMCacheService)

        # Verify system prompt builder
        from doc_ai_helper_backend.services.llm.utils.messaging import (
            JapaneseSystemPromptBuilder,
        )

        assert isinstance(
            common_service.system_prompt_builder, JapaneseSystemPromptBuilder
        )

        # Verify function manager
        from doc_ai_helper_backend.services.llm.utils.functions import (
            FunctionCallManager,
        )

        assert isinstance(common_service.function_manager, FunctionCallManager)

    @pytest.mark.asyncio
    async def test_query_basic(self, common_service, mock_service):
        """Test basic query functionality."""
        response = await common_service.query(
            service=mock_service, prompt="Test prompt"
        )

        # Verify response
        assert isinstance(response, LLMResponse)
        assert response.content == "Mock response"
        assert response.model == "mock-model"
        assert response.provider == "mock"

        # Verify mock service was called correctly
        assert len(mock_service.prepare_options_calls) == 1
        assert len(mock_service.call_api_calls) == 1
        assert len(mock_service.convert_response_calls) == 1

        # Verify correct prompt was passed
        assert mock_service.prepare_options_calls[0]["prompt"] == "Test prompt"

    @pytest.mark.asyncio
    async def test_query_with_options(self, common_service, mock_service):
        """Test query with custom options."""
        options = {"temperature": 0.8, "max_tokens": 100}

        response = await common_service.query(
            service=mock_service, prompt="Test prompt", options=options
        )

        assert isinstance(response, LLMResponse)

        # Verify options were passed through
        prepare_call = mock_service.prepare_options_calls[0]
        assert prepare_call["options"] == options

    @pytest.mark.asyncio
    async def test_query_with_conversation_history(
        self, common_service, mock_service, sample_message_history
    ):
        """Test query with conversation history."""
        response = await common_service.query(
            service=mock_service,
            prompt="Follow-up question",
            conversation_history=sample_message_history,
        )

        assert isinstance(response, LLMResponse)

        # Verify conversation history was passed
        prepare_call = mock_service.prepare_options_calls[0]
        assert prepare_call["conversation_history"] == sample_message_history

    @pytest.mark.asyncio
    async def test_query_caching(self, common_service, mock_service):
        """Test that query results are cached and retrieved properly."""
        prompt = "Cacheable prompt"

        # First call
        response1 = await common_service.query(service=mock_service, prompt=prompt)

        # Second call with same prompt - should use cache
        response2 = await common_service.query(service=mock_service, prompt=prompt)

        # Both responses should be identical
        assert response1.content == response2.content
        assert response1.model == response2.model

        # Mock service should only be called once (second time uses cache)
        assert len(mock_service.prepare_options_calls) == 1

    @pytest.mark.asyncio
    async def test_query_error_handling(self, common_service, mock_service):
        """Test query error handling."""

        # Mock an error in provider API call
        async def error_api_call(options):
            raise Exception("API error")

        mock_service._call_provider_api = error_api_call

        with pytest.raises(LLMServiceException) as exc_info:
            await common_service.query(service=mock_service, prompt="Error prompt")

        assert "Query orchestration failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_stream_query(self, common_service, mock_service):
        """Test streaming query functionality."""
        chunks = []
        async for chunk in common_service.stream_query(
            service=mock_service, prompt="Streaming prompt"
        ):
            chunks.append(chunk)

        # Verify we got the expected chunks
        assert chunks == ["Mock ", "streaming ", "response"]

        # Verify mock service was called correctly
        assert len(mock_service.prepare_options_calls) == 1
        assert len(mock_service.stream_api_calls) == 1

        # Verify correct prompt was passed
        assert mock_service.prepare_options_calls[0]["prompt"] == "Streaming prompt"

    @pytest.mark.asyncio
    async def test_stream_query_error_handling(self, common_service, mock_service):
        """Test streaming query error handling."""

        # Mock an error in streaming API
        async def error_stream_api(options):
            raise Exception("Streaming error")
            yield  # This makes it a generator but will never be reached

        mock_service._stream_provider_api = error_stream_api

        with pytest.raises(LLMServiceException) as exc_info:
            async for chunk in common_service.stream_query(
                service=mock_service, prompt="Error prompt"
            ):
                pass  # Should not reach here

        assert "Streaming query orchestration failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_query_with_tools(self, common_service, mock_service, sample_tools):
        """Test query with tools functionality."""
        response = await common_service.query_with_tools(
            service=mock_service, prompt="Use tools prompt", tools=sample_tools
        )

        assert isinstance(response, LLMResponse)
        assert response.content == "Mock response"

        # Verify tools were passed through
        prepare_call = mock_service.prepare_options_calls[0]
        assert prepare_call["tools"] == sample_tools
        assert prepare_call["prompt"] == "Use tools prompt"

    @pytest.mark.asyncio
    async def test_query_with_tools_and_choice(
        self, common_service, mock_service, sample_tools
    ):
        """Test query with tools and tool choice."""
        tool_choice = "auto"

        response = await common_service.query_with_tools(
            service=mock_service,
            prompt="Use specific tools",
            tools=sample_tools,
            tool_choice=tool_choice,
        )

        assert isinstance(response, LLMResponse)

        # Verify tool choice was passed
        prepare_call = mock_service.prepare_options_calls[0]
        assert prepare_call["tool_choice"] == tool_choice

    @pytest.mark.asyncio
    async def test_query_with_tools_error_handling(
        self, common_service, mock_service, sample_tools
    ):
        """Test query with tools error handling."""

        # Mock an error in provider API call
        async def error_api_call(options):
            raise Exception("Tools API error")

        mock_service._call_provider_api = error_api_call

        with pytest.raises(LLMServiceException) as exc_info:
            await common_service.query_with_tools(
                service=mock_service, prompt="Error prompt", tools=sample_tools
            )

        assert "Query with tools orchestration failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_system_prompt(self, common_service):
        """Test system prompt generation."""
        # Test that _generate_system_prompt method exists and can be called
        assert hasattr(common_service, "_generate_system_prompt")

        # Test basic system prompt generation
        system_prompt = await common_service._generate_system_prompt(
            repository_context=None,
            document_metadata=None,
            document_content=None,
            system_prompt_template="contextual_document_assistant_ja",
            include_document_in_system_prompt=True,
        )

        # Should return a string (even if empty or default)
        assert isinstance(system_prompt, (str, type(None)))

    @pytest.mark.asyncio
    async def test_query_full_workflow(
        self, common_service, mock_service, sample_message_history
    ):
        """Test complete query workflow with all parameters."""
        options = {"temperature": 0.7, "max_tokens": 150}

        response = await common_service.query(
            service=mock_service,
            prompt="Complex query",
            conversation_history=sample_message_history,
            options=options,
            system_prompt_template="default",
            include_document_in_system_prompt=False,
        )

        assert isinstance(response, LLMResponse)
        assert response.content == "Mock response"

        # Verify all parameters were passed correctly
        prepare_call = mock_service.prepare_options_calls[0]
        assert prepare_call["prompt"] == "Complex query"
        assert prepare_call["conversation_history"] == sample_message_history
        assert prepare_call["options"] == options

        # Verify service interaction flow
        assert len(mock_service.prepare_options_calls) == 1
        assert len(mock_service.call_api_calls) == 1
        assert len(mock_service.convert_response_calls) == 1
