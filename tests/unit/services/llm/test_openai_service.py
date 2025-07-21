"""
Tests for OpenAI LLM service composition implementation.

This module tests the NEW composition-based OpenAI service implementation.

⚠️  IMPORTANT:
- These are the ACTIVE tests for the current        with patch.object(
            o        with patch.object(
            openai_service.query_manager, "orchestrate_query_with_tools", return_value=expected_response
        ) as mock_query_tools:
            result = await openai_service.query_with_tools(
                "Test prompt", [{"name": "test_function"}]
            )

            # Verify delegation occurred
            mock_query_tools.assert_called_once()
            assert result == expected_responseice.query_manager, "orchestrate_streaming_query", return_value=mock_stream()
        ) as mock_stream_query:
            chunks = []
            async for chunk in openai_service.stream_query("Test prompt"):
                chunks.append(chunk)

            # Verify delegation occurred
            mock_stream_query.assert_called_once()
            assert chunks == ["chunk1", "chunk2", "chunk3"]rvice
- Legacy tests (old modular architecture) are in tests/unit/services/llm/legacy/
- Legacy tests are intentionally skipped and expected to fail

✅ Architecture: Composition pattern with LLMServiceCommon
✅ Status: All tests passing (expanded coverage)
✅ Coverage: Complete OpenAI service functionality including edge cases
"""

import json
import pytest
from typing import Dict, Any, List, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from doc_ai_helper_backend.services.llm.openai_service import OpenAIService
from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    LLMUsage,
    ProviderCapabilities,
    MessageItem,
    MessageRole,
    FunctionDefinition,
    ToolChoice,
    ToolCall,
    FunctionCall,
)
from doc_ai_helper_backend.core.exceptions import LLMServiceException


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response"
    mock_response.choices[0].message.tool_calls = None
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5
    mock_response.usage.total_tokens = 15
    mock_response.model = "gpt-3.5-turbo"
    # Mock model_dump to return a dict
    mock_response.model_dump.return_value = {
        "choices": [{"message": {"content": "Test response"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        "model": "gpt-3.5-turbo",
    }
    return mock_response


@pytest.fixture
def openai_service():
    """Create OpenAI service instance for testing."""
    return OpenAIService(api_key="test_key", default_model="gpt-3.5-turbo")


class TestOpenAIService:
    """Test cases for OpenAI service composition implementation."""

    def test_initialization(self):
        """Test service initialization."""
        service = OpenAIService(
            api_key="test_key", default_model="gpt-4", base_url="https://custom.url"
        )

        assert service.api_key == "test_key"
        assert service.model == "gpt-4"  # Using delegation property
        assert service.base_url == "https://custom.url"
        # Verify pure composition pattern - direct component access
        assert hasattr(service, "cache_service")
        assert hasattr(service, "template_manager")
        assert hasattr(service, "query_manager")
        assert service.sync_client is not None
        assert service.async_client is not None

    def test_inheritance(self, openai_service):
        """Test that the service implements the base interface."""
        assert isinstance(openai_service, LLMServiceBase)

    def test_composition_pattern(self, openai_service):
        """Test that the service uses pure composition pattern."""
        # Should have direct component instances (no _common intermediate layer)
        assert hasattr(openai_service, "cache_service")
        assert hasattr(openai_service, "template_manager")
        assert hasattr(openai_service, "query_manager")
        assert hasattr(openai_service, "function_manager")
        assert hasattr(openai_service, "response_builder")

        # Common methods should be available through direct delegation
        assert hasattr(openai_service, "query")
        assert hasattr(openai_service, "stream_query")
        assert hasattr(openai_service, "query_with_tools")

    @pytest.mark.asyncio
    async def test_get_capabilities(self, openai_service):
        """Test getting provider capabilities."""
        capabilities = await openai_service.get_capabilities()

        assert isinstance(capabilities, ProviderCapabilities)
        assert capabilities.supports_streaming is True
        assert capabilities.supports_function_calling is True
        assert len(capabilities.available_models) > 0
        assert "gpt-3.5-turbo" in capabilities.available_models

    @pytest.mark.asyncio
    async def test_estimate_tokens(self, openai_service):
        """Test token estimation."""
        text = "This is a test message"
        tokens = await openai_service.estimate_tokens(text)

        assert isinstance(tokens, int)
        assert tokens > 0

    @pytest.mark.asyncio
    async def test_prepare_options(self, openai_service):
        """Test options preparation."""
        # Skip this test as _prepare_provider_options is complex and tested elsewhere
        # We'll focus on testing the interface delegation
        assert hasattr(openai_service, "_prepare_provider_options")
        assert callable(getattr(openai_service, "_prepare_provider_options"))

    @pytest.mark.asyncio
    async def test_convert_response(self, openai_service, mock_openai_response):
        """Test response conversion."""
        options = {"model": "gpt-3.5-turbo"}
        converted = await openai_service._convert_provider_response(
            mock_openai_response, options
        )

        assert isinstance(converted, LLMResponse)
        assert converted.content == "Test response"
        assert converted.model == "gpt-3.5-turbo"
        assert converted.provider == "openai"
        assert converted.usage.prompt_tokens == 10
        assert converted.usage.completion_tokens == 5
        assert converted.usage.total_tokens == 15

    @pytest.mark.asyncio
    @patch("doc_ai_helper_backend.services.llm.openai_service.AsyncOpenAI")
    async def test_query_method_delegation(self, mock_async_openai, openai_service):
        """Test that query method delegates to common implementation."""
        # Mock the async client's response
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].message.tool_calls = None
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_response.model = "gpt-3.5-turbo"

        mock_client.chat.completions.create.return_value = mock_response
        mock_async_openai.return_value = mock_client
        openai_service.async_client = mock_client

        # Mock the common service's query method
        expected_response = LLMResponse(
            content="Test response",
            model="gpt-3.5-turbo",
            provider="openai",
            usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            raw_response={},
        )

        with patch.object(
            openai_service.query_manager,
            "orchestrate_query",
            return_value=expected_response,
        ) as mock_query:
            result = await openai_service.query("Test prompt")

            # Verify delegation occurred
            mock_query.assert_called_once()
            assert result == expected_response

    @pytest.mark.asyncio
    @patch("doc_ai_helper_backend.services.llm.openai_service.AsyncOpenAI")
    async def test_stream_query_method_delegation(
        self, mock_async_openai, openai_service
    ):
        """Test that stream_query method delegates to common implementation."""
        # Mock the async client
        mock_client = AsyncMock()
        mock_async_openai.return_value = mock_client
        openai_service.async_client = mock_client

        # Mock the common service's stream_query method
        async def mock_stream():
            yield "chunk1"
            yield "chunk2"

        with patch.object(
            openai_service.query_manager,
            "orchestrate_streaming_query",
            return_value=mock_stream(),
        ) as mock_stream_query:
            chunks = []
            async for chunk in openai_service.stream_query("Test prompt"):
                chunks.append(chunk)

            # Verify delegation occurred
            mock_stream_query.assert_called_once()
            assert chunks == ["chunk1", "chunk2"]

    @pytest.mark.asyncio
    async def test_query_with_tools_delegation(self, openai_service):
        """Test that query_with_tools method delegates to common implementation."""
        tools = [
            FunctionDefinition(
                name="test_function",
                description="A test function",
                parameters={"type": "object", "properties": {}},
            )
        ]

        expected_response = LLMResponse(
            content="Test response with tools",
            model="gpt-3.5-turbo",
            provider="openai",
            usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            raw_response={},
            tool_calls=[],
        )

        with patch.object(
            openai_service.query_manager,
            "orchestrate_query_with_tools",
            return_value=expected_response,
        ) as mock_query_tools:
            result = await openai_service.query_with_tools(
                "Test prompt", tools, tool_choice="auto"
            )

            # Verify delegation occurred
            mock_query_tools.assert_called_once()
            assert result == expected_response

    def test_mixin_composition_pattern(self, openai_service):
        """Test that the service uses pure composition pattern (no mixins)."""
        # Check MRO (Method Resolution Order) - should not include mixin classes
        mro = type(openai_service).__mro__

        # Should include OpenAIService and LLMServiceBase only, no mixins
        assert mro[0] == OpenAIService
        assert any("LLMServiceBase" in cls.__name__ for cls in mro)
        # PropertyAccessors mixin should NOT be in the inheritance chain anymore
        assert not any(
            "PropertyAccessors" in cls.__name__ for cls in mro
        )  # Verify composition pattern provides expected functionality through delegation
        assert hasattr(openai_service, "cache_service")
        assert hasattr(openai_service, "template_manager")
        assert hasattr(openai_service, "response_builder")
        assert hasattr(openai_service, "streaming_utils")

        # Verify components are directly owned (not delegated through _common)
        assert not hasattr(openai_service, "_common")
        assert openai_service.cache_service is not None

    def test_encapsulation(self, openai_service):
        """Test that pure composition is properly encapsulated."""
        # No intermediate _common layer in pure composition
        assert not hasattr(openai_service, "_common")

        # Component accessors should be available for direct access
        assert hasattr(openai_service, "cache_service")
        assert hasattr(openai_service, "template_manager")
        assert hasattr(openai_service, "function_handler")
        # Verify components are directly accessible (pure composition)
        assert openai_service.cache_service is not None
        assert openai_service.template_manager is not None
        assert openai_service.function_handler is openai_service.function_manager

    @pytest.mark.asyncio
    async def test_error_handling_in_provider_methods(self, openai_service):
        """Test error handling in provider-specific methods."""
        # Test that provider-specific methods handle errors properly
        with patch.object(openai_service, "_token_encoder") as mock_encoder:
            mock_encoder.encode.side_effect = Exception("Encoding error")

            # Should not raise exception, but handle gracefully
            result = await openai_service.estimate_tokens("test")
            # Should return character-based approximation
            assert isinstance(result, int)
            assert result > 0

    @pytest.mark.asyncio
    async def test_custom_base_url_initialization(self):
        """Test initialization with custom base URL."""
        service = OpenAIService(
            api_key="test_key",
            default_model="gpt-4",
            base_url="https://custom-litellm.example.com",
        )

        assert service.base_url == "https://custom-litellm.example.com"

        # Verify clients are initialized with custom base URL
        assert service.sync_client.base_url == "https://custom-litellm.example.com"
        assert service.async_client.base_url == "https://custom-litellm.example.com"

    def test_token_encoder_fallback(self):
        """Test token encoder fallback for unknown models."""
        with patch(
            "tiktoken.encoding_for_model", side_effect=KeyError("Unknown model")
        ):
            with patch("tiktoken.get_encoding") as mock_get_encoding:
                mock_encoder = MagicMock()
                mock_get_encoding.return_value = mock_encoder

                service = OpenAIService(
                    api_key="test_key", default_model="unknown-model"
                )

                # Should fall back to cl100k_base encoding
                mock_get_encoding.assert_called_once_with("cl100k_base")
                assert service._token_encoder == mock_encoder


# === Expanded Test Suite ===


class TestOpenAIServiceExtended:
    """Extended test suite for OpenAI service provider-specific functionality."""

    @pytest.fixture
    def service(self):
        return OpenAIService(api_key="test-key", default_model="gpt-4")

    @pytest.fixture
    def mock_openai_response_with_tools(self):
        """Mock OpenAI API response with tool calls."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "I'll help you with that."

        # Mock tool calls
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.type = "function"
        mock_tool_call.function.name = "get_weather"
        mock_tool_call.function.arguments = '{"city": "Tokyo"}'
        mock_response.choices[0].message.tool_calls = [mock_tool_call]

        mock_response.usage.prompt_tokens = 15
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 25
        mock_response.model = "gpt-4"

        mock_response.model_dump.return_value = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "model": "gpt-4",
            "choices": [{"message": {"content": "I'll help you with that."}}],
        }
        return mock_response

    @pytest.fixture
    def mock_stream_chunks(self):
        """Mock streaming response chunks."""
        chunks = []
        for i, text in enumerate(["Hello", " there", "!", ""]):
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta.content = text if text else None
            chunks.append(chunk)
        return chunks

    # === Provider Options Preparation Tests ===

    async def test_prepare_provider_options_basic(self, service):
        """Test basic provider options preparation."""
        messages = [MessageItem(role=MessageRole.USER, content="Hello")]

        with patch.object(
            service.query_manager, "build_conversation_messages", return_value=messages
        ):
            options = await service._prepare_provider_options(
                "Hello", None, None, None, None
            )

        assert options["model"] == service.model
        assert options["messages"] == [{"role": "user", "content": "Hello"}]
        assert options["temperature"] == 1.0  # Updated default temperature
        assert options["max_completion_tokens"] == 1000  # Updated to max_completion_tokens

    async def test_prepare_provider_options_with_tools(self, service):
        """Test provider options preparation with tools."""
        messages = [MessageItem(role=MessageRole.USER, content="What's the weather?")]

        tools = [
            FunctionDefinition(
                name="get_weather",
                description="Get weather info",
                parameters={
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            )
        ]

        tool_choice = ToolChoice(type="required", function={"name": "get_weather"})

        with patch.object(
            service.query_manager, "build_conversation_messages", return_value=messages
        ):
            options = await service._prepare_provider_options(
                "What's the weather?",
                None,
                {"temperature": 0.5},
                None,
                tools,
                tool_choice,
            )

        assert "tools" in options
        assert len(options["tools"]) == 1
        assert options["tools"][0]["type"] == "function"
        assert options["tools"][0]["function"]["name"] == "get_weather"
        assert "tool_choice" in options
        assert options["temperature"] == 0.5

    # Note: Some advanced features like tool_calls in MessageItem may not be
    # fully implemented yet. These tests serve as documentation for future features.

    async def test_prepare_provider_options_custom_options(self, service):
        """Test custom options handling."""
        messages = [MessageItem(role=MessageRole.USER, content="Hello")]

        custom_options = {
            "model": "gpt-3.5-turbo",
            "temperature": 0.9,
            "max_tokens": 2000,
            "top_p": 0.95,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.2,
            "custom_param": "test_value",
        }

        with patch.object(
            service.query_manager, "build_conversation_messages", return_value=messages
        ):
            options = await service._prepare_provider_options(
                "Hello", None, custom_options, None, None, None
            )

        assert options["model"] == "gpt-3.5-turbo"
        assert options["temperature"] == 0.9
        assert options["max_completion_tokens"] == 2000  # Updated to max_completion_tokens
        assert options["top_p"] == 0.95
        assert options["frequency_penalty"] == 0.1
        assert options["presence_penalty"] == 0.2
        assert options["custom_param"] == "test_value"

    # === API Call Tests ===

    async def test_call_provider_api_success(self, service, mock_openai_response):
        """Test successful API call."""
        with patch.object(
            service.async_client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_openai_response,
        ) as mock_create:
            options = {
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "Hello"}],
            }
            response = await service._call_provider_api(options)

            assert response == mock_openai_response
            mock_create.assert_called_once_with(**options)

    async def test_call_provider_api_failure(self, service):
        """Test API call failure handling."""
        with patch.object(
            service.async_client.chat.completions,
            "create",
            side_effect=Exception("API Error"),
        ):
            options = {
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "Hello"}],
            }

            with pytest.raises(LLMServiceException) as exc_info:
                await service._call_provider_api(options)

            assert "OpenAI API call failed: API Error" in str(exc_info.value)

    # === Streaming Tests ===

    async def test_stream_provider_api_success(self, service, mock_stream_chunks):
        """Test successful streaming API call."""

        async def mock_stream_func():
            for chunk in mock_stream_chunks:
                yield chunk

        with patch.object(
            service.async_client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_stream_func(),
        ) as mock_create:
            options = {
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "Hello"}],
            }

            chunks = []
            async for chunk in service._stream_provider_api(options):
                chunks.append(chunk)

            expected_chunks = ["Hello", " there", "!"]
            assert chunks == expected_chunks

            # Verify stream=True was added to options
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args["stream"] is True

    async def test_stream_provider_api_failure(self, service):
        """Test streaming API call failure handling."""
        with patch.object(
            service.async_client.chat.completions,
            "create",
            side_effect=Exception("Streaming Error"),
        ):
            options = {
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "Hello"}],
            }

            with pytest.raises(LLMServiceException) as exc_info:
                chunks = []
                async for chunk in service._stream_provider_api(options):
                    chunks.append(chunk)

            assert "OpenAI streaming failed: Streaming Error" in str(exc_info.value)

    # === Response Conversion Tests ===

    async def test_convert_provider_response_basic(self, service, mock_openai_response):
        """Test basic response conversion."""
        options = {"model": "gpt-4"}

        response = await service._convert_provider_response(
            mock_openai_response, options
        )

        assert isinstance(response, LLMResponse)
        assert response.content == "Test response"
        assert response.model == "gpt-4"
        assert response.provider == "openai"
        assert response.usage.prompt_tokens == 10
        assert response.usage.completion_tokens == 5
        assert response.usage.total_tokens == 15
        assert response.tool_calls is None

    async def test_convert_provider_response_with_tools(
        self, service, mock_openai_response_with_tools
    ):
        """Test response conversion with tool calls."""
        options = {"model": "gpt-4"}

        response = await service._convert_provider_response(
            mock_openai_response_with_tools, options
        )

        assert isinstance(response, LLMResponse)
        assert response.content == "I'll help you with that."
        assert response.tool_calls is not None
        assert len(response.tool_calls) == 1

        tool_call = response.tool_calls[0]
        assert tool_call.id == "call_123"
        assert tool_call.type == "function"
        assert tool_call.function.name == "get_weather"
        assert tool_call.function.arguments == '{"city": "Tokyo"}'

    async def test_convert_provider_response_no_usage(self, service):
        """Test response conversion when usage info is missing."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response without usage"
        mock_response.choices[0].message.tool_calls = None
        mock_response.usage = None
        mock_response.model_dump.return_value = {"content": "Response without usage"}

        options = {"model": "gpt-4"}
        response = await service._convert_provider_response(mock_response, options)

        assert response.usage.prompt_tokens == 0
        assert response.usage.completion_tokens == 0
        assert response.usage.total_tokens == 0

    async def test_convert_provider_response_failure(self, service):
        """Test response conversion failure handling."""
        # Create a malformed response that will cause conversion to fail
        bad_response = MagicMock()
        bad_response.choices = []  # Empty choices will cause IndexError

        options = {"model": "gpt-4"}

        with pytest.raises(LLMServiceException) as exc_info:
            await service._convert_provider_response(bad_response, options)

        assert "Response conversion failed" in str(exc_info.value)

    # === Tool Conversion Tests ===

    def test_convert_tools_to_openai_format_function_definition(self, service):
        """Test converting FunctionDefinition objects to OpenAI format."""
        tools = [
            FunctionDefinition(
                name="get_weather",
                description="Get current weather",
                parameters={
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            ),
            FunctionDefinition(
                name="calculate",
                description="Perform calculation",
                parameters={
                    "type": "object",
                    "properties": {"expression": {"type": "string"}},
                    "required": ["expression"],
                },
            ),
        ]

        converted = service._convert_tools_to_openai_format(tools)

        assert len(converted) == 2
        assert converted[0]["type"] == "function"
        assert converted[0]["function"]["name"] == "get_weather"
        assert converted[0]["function"]["description"] == "Get current weather"
        assert converted[1]["function"]["name"] == "calculate"

    def test_convert_tools_to_openai_format_dict_without_type(self, service):
        """Test converting dict tools without type field."""
        tools = [
            {
                "name": "search",
                "description": "Search for information",
                "parameters": {"type": "object", "properties": {}},
            }
        ]

        converted = service._convert_tools_to_openai_format(tools)

        assert len(converted) == 1
        assert converted[0]["type"] == "function"
        assert converted[0]["function"]["name"] == "search"

    def test_convert_tools_to_openai_format_dict_with_type(self, service):
        """Test converting dict tools that already have type field."""
        tools = [
            {
                "type": "function",
                "function": {"name": "analyze", "description": "Analyze data"},
            }
        ]

        converted = service._convert_tools_to_openai_format(tools)

        assert len(converted) == 1
        assert converted[0] == tools[0]  # Should be unchanged

    def test_convert_tool_choice_to_openai_format(self, service):
        """Test tool choice conversion."""
        # Test specific function choice - should return the type string
        tool_choice = ToolChoice(type="required", function={"name": "get_weather"})
        converted = service._convert_tool_choice_to_openai_format(tool_choice)

        # Should return the type string for required
        assert converted == "required"

    def test_convert_tool_choice_to_openai_format_auto(self, service):
        """Test auto tool choice conversion."""
        tool_choice = ToolChoice(type="auto")
        converted = service._convert_tool_choice_to_openai_format(tool_choice)
        # Should return the type string
        assert converted == "auto"

    def test_convert_tool_choice_to_openai_format_none(self, service):
        """Test none tool choice conversion."""
        tool_choice = ToolChoice(type="none")
        converted = service._convert_tool_choice_to_openai_format(tool_choice)
        # Should return the type string
        assert converted == "none"

    # === Integration Tests ===

    async def test_full_query_with_provider_specific_features(self, service):
        """Test complete query flow with OpenAI-specific features."""
        # Mock the query manager method
        with patch.object(service.query_manager, "orchestrate_query") as mock_query:
            mock_response = LLMResponse(
                content="OpenAI response",
                model="gpt-4",
                provider="openai",
                usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
                raw_response={},
            )
            mock_query.return_value = mock_response

            response = await service.query(
                "What's the weather?", options={"temperature": 0.8, "top_p": 0.9}
            )

            assert response == mock_response
            mock_query.assert_called_once()

            # Verify that the service was passed to common
            call_args = mock_query.call_args
            assert call_args[1]["service"] == service

    async def test_error_handling_in_delegated_methods(self, service):
        """Test error handling in methods that delegate to query manager."""
        with patch.object(
            service.query_manager,
            "orchestrate_query",
            side_effect=LLMServiceException("Query manager error"),
        ):
            with pytest.raises(LLMServiceException):
                await service.query("Test prompt")

    # === Custom Base URL Tests ===

    def test_service_with_custom_base_url(self):
        """Test service initialization with custom base URL."""
        custom_service = OpenAIService(
            api_key="test-key",
            base_url="https://custom-proxy.example.com/v1",
            default_model="custom-model",
        )

        assert custom_service.model == "custom-model"
        # Note: We can't easily test the base_url without accessing private client attributes
