"""
Test suite for OpenAIService

Comprehensive tests for the OpenAI LLM service implementation,
including provider-specific functionality, tool integration, and MCP support.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from doc_ai_helper_backend.services.llm.providers.openai_service import OpenAIService
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
def mock_openai_client():
    """Create a mock OpenAI async client."""
    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    mock_client.chat.completions.create = AsyncMock()
    return mock_client


@pytest.fixture
def openai_service():
    """Create OpenAIService instance with mocked dependencies."""
    with patch('doc_ai_helper_backend.services.llm.providers.openai_service.AsyncOpenAI') as mock_openai:
        with patch('doc_ai_helper_backend.services.llm.providers.openai_service.tiktoken') as mock_tiktoken:
            # Mock tiktoken encoder
            mock_encoder = Mock()
            mock_encoder.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
            mock_tiktoken.encoding_for_model.return_value = mock_encoder
            
            # Mock the async client properly
            mock_client = Mock()
            mock_client.chat = Mock()
            mock_client.chat.completions = Mock()
            mock_client.chat.completions.create = AsyncMock()
            mock_openai.return_value = mock_client
            
            service = OpenAIService(api_key="test-key", default_model="gpt-3.5-turbo")
            return service


@pytest.fixture
def sample_openai_response():
    """Create a sample OpenAI API response."""
    response = Mock()
    response.model = "gpt-3.5-turbo"
    response.choices = [Mock()]
    response.choices[0].message = Mock()
    response.choices[0].message.content = "Test response content"
    response.choices[0].message.tool_calls = None  # No tool calls by default
    response.choices[0].finish_reason = "stop"
    response.usage = Mock()
    response.usage.prompt_tokens = 10
    response.usage.completion_tokens = 15
    response.usage.total_tokens = 25
    return response


class TestOpenAIServiceInitialization:
    """Test OpenAI service initialization."""

    @patch('doc_ai_helper_backend.services.llm.providers.openai_service.AsyncOpenAI')
    @patch('doc_ai_helper_backend.services.llm.providers.openai_service.tiktoken')
    def test_basic_initialization(self, mock_tiktoken, mock_openai):
        """Test basic service initialization."""
        mock_encoder = Mock()
        mock_tiktoken.encoding_for_model.return_value = mock_encoder
        
        service = OpenAIService(api_key="test-key")
        
        assert service.api_key == "test-key"
        assert service.default_model == "gpt-3.5-turbo"
        assert service.base_url is None
        assert service._mcp_server is None
        mock_openai.assert_called_once_with(api_key="test-key")
        mock_tiktoken.encoding_for_model.assert_called_once_with("gpt-3.5-turbo")

    @patch('doc_ai_helper_backend.services.llm.providers.openai_service.AsyncOpenAI')
    @patch('doc_ai_helper_backend.services.llm.providers.openai_service.tiktoken')
    def test_initialization_with_custom_params(self, mock_tiktoken, mock_openai):
        """Test initialization with custom parameters."""
        mock_encoder = Mock()
        mock_tiktoken.encoding_for_model.return_value = mock_encoder
        
        service = OpenAIService(
            api_key="custom-key", 
            default_model="gpt-4",
            base_url="https://custom-url.com",
            temperature=0.7
        )
        
        assert service.api_key == "custom-key"
        assert service.default_model == "gpt-4"
        assert service.base_url == "https://custom-url.com"
        assert service.default_options == {"temperature": 0.7}
        
        mock_openai.assert_called_once_with(
            api_key="custom-key", 
            base_url="https://custom-url.com"
        )

    @patch('doc_ai_helper_backend.services.llm.providers.openai_service.AsyncOpenAI')
    @patch('doc_ai_helper_backend.services.llm.providers.openai_service.tiktoken')
    def test_encoder_fallback(self, mock_tiktoken, mock_openai):
        """Test encoder fallback when model-specific encoder is not available."""
        mock_tiktoken.encoding_for_model.side_effect = KeyError("Model not found")
        mock_fallback_encoder = Mock()
        mock_tiktoken.get_encoding.return_value = mock_fallback_encoder
        
        service = OpenAIService(api_key="test-key", default_model="custom-model")
        
        mock_tiktoken.get_encoding.assert_called_once_with("cl100k_base")
        assert service._token_encoder == mock_fallback_encoder


class TestOpenAIServiceCapabilities:
    """Test OpenAI service capabilities and token estimation."""

    async def test_get_capabilities(self, openai_service):
        """Test getting provider capabilities."""
        capabilities = await openai_service.get_capabilities()
        
        assert isinstance(capabilities, ProviderCapabilities)
        assert "gpt-3.5-turbo" in capabilities.available_models
        assert "gpt-4" in capabilities.available_models
        assert "gpt-4o" in capabilities.available_models
        assert capabilities.max_tokens["gpt-3.5-turbo"] == 4096
        assert capabilities.max_tokens["gpt-4o"] == 128000
        assert capabilities.supports_streaming is True
        assert capabilities.supports_function_calling is True

    async def test_estimate_tokens_success(self, openai_service):
        """Test successful token estimation."""
        tokens = await openai_service.estimate_tokens("Test text")
        
        assert tokens == 5  # Mock encoder returns [1,2,3,4,5]
        openai_service._token_encoder.encode.assert_called_once_with("Test text")

    async def test_estimate_tokens_fallback(self, openai_service):
        """Test token estimation fallback when encoder fails."""
        openai_service._token_encoder.encode.side_effect = Exception("Encoding failed")
        
        tokens = await openai_service.estimate_tokens("Test text with 20 chars")
        
        # Should fall back to character/4 approximation: 20 // 4 = 5
        assert tokens == 5


class TestOpenAIServiceMCP:
    """Test MCP server integration."""

    def test_set_mcp_server(self, openai_service):
        """Test setting MCP server."""
        mock_server = Mock()
        
        openai_service.set_mcp_server(mock_server)
        
        assert openai_service._mcp_server == mock_server
        assert openai_service.get_mcp_server() == mock_server

    def test_set_mcp_server_none(self, openai_service):
        """Test setting MCP server to None."""
        openai_service.set_mcp_server(None)
        
        assert openai_service._mcp_server is None
        assert openai_service.get_mcp_server() is None


class TestOpenAIServiceProviderOptions:
    """Test provider-specific option preparation."""

    async def test_prepare_provider_options_basic(self, openai_service):
        """Test basic provider options preparation."""
        options = await openai_service._prepare_provider_options(
            prompt="Test prompt"
        )
        
        assert options["model"] == "gpt-3.5-turbo"
        assert options["temperature"] == 1.0
        assert options["max_completion_tokens"] == 1000
        assert len(options["messages"]) == 1
        assert options["messages"][0]["role"] == "user"
        assert options["messages"][0]["content"] == "Test prompt"

    async def test_prepare_provider_options_with_system_prompt(self, openai_service):
        """Test provider options with system prompt."""
        options = await openai_service._prepare_provider_options(
            prompt="User question",
            system_prompt="You are a helpful assistant"
        )
        
        assert len(options["messages"]) == 2
        assert options["messages"][0]["role"] == "system"
        assert options["messages"][0]["content"] == "You are a helpful assistant"
        assert options["messages"][1]["role"] == "user"
        assert options["messages"][1]["content"] == "User question"

    async def test_prepare_provider_options_with_conversation_history(self, openai_service):
        """Test provider options with conversation history."""
        history = [
            MessageItem(role=MessageRole.USER, content="Previous question"),
            MessageItem(role=MessageRole.ASSISTANT, content="Previous answer")
        ]
        
        options = await openai_service._prepare_provider_options(
            prompt="Current question",
            conversation_history=history
        )
        
        assert len(options["messages"]) == 3
        assert options["messages"][0]["role"] == "user"
        assert options["messages"][0]["content"] == "Previous question"
        assert options["messages"][1]["role"] == "assistant"
        assert options["messages"][1]["content"] == "Previous answer"
        assert options["messages"][2]["role"] == "user" 
        assert options["messages"][2]["content"] == "Current question"

    async def test_prepare_provider_options_with_tools(self, openai_service):
        """Test provider options with tools."""
        tools = [
            FunctionDefinition(
                name="test_function",
                description="A test function",
                parameters={"type": "object", "properties": {"arg": {"type": "string"}}}
            )
        ]
        tool_choice = ToolChoice(type="auto")
        
        options = await openai_service._prepare_provider_options(
            prompt="Test with tools",
            tools=tools,
            tool_choice=tool_choice
        )
        
        assert "tools" in options
        assert len(options["tools"]) == 1
        assert options["tools"][0]["type"] == "function"
        assert options["tools"][0]["function"]["name"] == "test_function"
        assert options["tool_choice"] == "auto"

    async def test_prepare_provider_options_custom_model_and_params(self, openai_service):
        """Test provider options with custom model and parameters."""
        custom_options = {
            "model": "gpt-4",
            "temperature": 0.5,
            "max_tokens": 2000,
            "top_p": 0.9
        }
        
        options = await openai_service._prepare_provider_options(
            prompt="Test prompt",
            options=custom_options
        )
        
        assert options["model"] == "gpt-4"
        assert options["temperature"] == 0.5
        assert options["max_completion_tokens"] == 2000
        assert options["top_p"] == 0.9


class TestOpenAIServiceAPICall:
    """Test OpenAI API calls."""

    async def test_call_provider_api_success(self, openai_service, sample_openai_response):
        """Test successful API call."""
        openai_service.async_client.chat.completions.create.return_value = sample_openai_response
        
        options = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "test"}]}
        response = await openai_service._call_provider_api(options)
        
        assert response == sample_openai_response
        openai_service.async_client.chat.completions.create.assert_called_once_with(**options)

    async def test_call_provider_api_with_tools(self, openai_service, sample_openai_response):
        """Test API call with tools."""
        # Mock tool calls in response
        tool_call = Mock()
        tool_call.function.name = "test_function"
        sample_openai_response.choices[0].message.tool_calls = [tool_call]
        
        openai_service.async_client.chat.completions.create.return_value = sample_openai_response
        
        options = {
            "model": "gpt-3.5-turbo", 
            "messages": [{"role": "user", "content": "test"}],
            "tools": [{"type": "function", "function": {"name": "test_function"}}]
        }
        response = await openai_service._call_provider_api(options)
        
        assert response == sample_openai_response

    async def test_call_provider_api_failure(self, openai_service):
        """Test API call failure."""
        openai_service.async_client.chat.completions.create.side_effect = Exception("API Error")
        
        options = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "test"}]}
        
        with pytest.raises(LLMServiceException, match="OpenAI API call failed: API Error"):
            await openai_service._call_provider_api(options)

    async def test_stream_provider_api_success(self, openai_service):
        """Test successful streaming API call."""
        # Mock streaming response
        mock_chunk1 = Mock()
        mock_chunk1.choices = [Mock()]
        mock_chunk1.choices[0].delta.content = "Hello"
        
        mock_chunk2 = Mock()
        mock_chunk2.choices = [Mock()]
        mock_chunk2.choices[0].delta.content = " world"
        
        mock_chunk3 = Mock()  # Empty chunk
        mock_chunk3.choices = [Mock()]
        mock_chunk3.choices[0].delta.content = None
        
        async def mock_stream():
            yield mock_chunk1
            yield mock_chunk2
            yield mock_chunk3
        
        openai_service.async_client.chat.completions.create.return_value = mock_stream()
        
        options = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "test"}]}
        
        chunks = []
        async for chunk in openai_service._stream_provider_api(options):
            chunks.append(chunk)
        
        assert chunks == ["Hello", " world"]
        # Verify stream=True was added to options
        call_args = openai_service.async_client.chat.completions.create.call_args[1]
        assert call_args["stream"] is True

    async def test_stream_provider_api_failure(self, openai_service):
        """Test streaming API call failure."""
        openai_service.async_client.chat.completions.create.side_effect = Exception("Stream Error")
        
        options = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "test"}]}
        
        with pytest.raises(LLMServiceException, match="OpenAI streaming failed: Stream Error"):
            async for chunk in openai_service._stream_provider_api(options):
                pass


class TestOpenAIServiceResponseConversion:
    """Test OpenAI response conversion."""

    async def test_convert_provider_response_basic(self, openai_service, sample_openai_response):
        """Test basic response conversion."""
        options = {"model": "gpt-3.5-turbo"}
        
        llm_response = await openai_service._convert_provider_response(sample_openai_response, options)
        
        assert isinstance(llm_response, LLMResponse)
        assert llm_response.content == "Test response content"
        assert llm_response.model == "gpt-3.5-turbo"
        assert llm_response.provider == "openai"
        assert llm_response.usage.prompt_tokens == 10
        assert llm_response.usage.completion_tokens == 15
        assert llm_response.usage.total_tokens == 25

    async def test_convert_provider_response_with_tool_calls(self, openai_service, sample_openai_response):
        """Test response conversion with tool calls."""
        # Mock tool calls
        tool_call = Mock()
        tool_call.id = "call_123"
        tool_call.function.name = "test_function"
        tool_call.function.arguments = '{"arg": "value"}'
        
        sample_openai_response.choices[0].message.tool_calls = [tool_call]
        
        options = {"model": "gpt-3.5-turbo"}
        llm_response = await openai_service._convert_provider_response(sample_openai_response, options)
        
        assert len(llm_response.tool_calls) == 1
        assert llm_response.tool_calls[0].id == "call_123"
        assert llm_response.tool_calls[0].function.name == "test_function"
        assert llm_response.tool_calls[0].function.arguments == '{"arg": "value"}'

    async def test_convert_provider_response_no_choices(self, openai_service):
        """Test response conversion with no choices."""
        response = Mock()
        response.choices = []
        
        options = {"model": "gpt-3.5-turbo"}
        
        with pytest.raises(LLMServiceException, match="No choices in OpenAI response"):
            await openai_service._convert_provider_response(response, options)

    async def test_convert_provider_response_no_usage(self, openai_service):
        """Test response conversion without usage information."""
        response = Mock()
        response.model = "gpt-3.5-turbo"
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = "Test content"
        response.choices[0].finish_reason = "stop"
        response.usage = None
        
        options = {"model": "gpt-3.5-turbo"}
        llm_response = await openai_service._convert_provider_response(response, options)
        
        assert llm_response.content == "Test content"
        # Usage should be default factory instance when not provided
        assert llm_response.usage is not None
        assert llm_response.usage.prompt_tokens == 0
        assert llm_response.usage.completion_tokens == 0
        assert llm_response.usage.total_tokens == 0

    async def test_convert_provider_response_conversion_failure(self, openai_service):
        """Test response conversion failure."""
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        # Simulate an error during conversion
        response.choices[0].message.content = None
        response.model = None  # This will cause an error
        
        options = {"model": "gpt-3.5-turbo"}
        
        with pytest.raises(LLMServiceException, match="Response conversion failed"):
            await openai_service._convert_provider_response(response, options)


class TestOpenAIServiceFunctionExecution:
    """Test function execution and MCP integration."""

    async def test_execute_function_call_with_mcp(self, openai_service):
        """Test function execution with MCP server."""
        mock_mcp_server = Mock()
        mock_mcp_server.call_tool = AsyncMock(return_value="Tool result")
        openai_service.set_mcp_server(mock_mcp_server)
        
        function_call = FunctionCall(name="test_function", arguments='{"arg": "value"}')
        available_functions = {}
        
        result = await openai_service.execute_function_call(function_call, available_functions)
        
        assert result["success"] is True
        assert result["result"] == "Tool result"
        assert result["error"] is None
        mock_mcp_server.call_tool.assert_called_once_with("test_function", arg="value")

    async def test_execute_function_call_with_repository_context(self, openai_service):
        """Test function execution with repository context."""
        mock_mcp_server = Mock()
        mock_mcp_server.call_tool = AsyncMock(return_value="Tool result")
        openai_service.set_mcp_server(mock_mcp_server)
        
        function_call = FunctionCall(name="test_function", arguments='{"arg": "value"}')
        available_functions = {}
        repository_context = {"service": "github", "owner": "test", "repo": "test"}
        
        result = await openai_service.execute_function_call(
            function_call, available_functions, repository_context
        )
        
        assert result["success"] is True
        mock_mcp_server.call_tool.assert_called_once_with(
            "test_function", 
            arg="value", 
            repository_context=repository_context
        )

    async def test_execute_function_call_git_tool_without_context(self, openai_service):
        """Test Git tool execution without repository context."""
        mock_mcp_server = Mock()
        openai_service.set_mcp_server(mock_mcp_server)
        
        function_call = FunctionCall(name="create_git_issue", arguments='{"title": "Test issue"}')
        available_functions = {}
        
        result = await openai_service.execute_function_call(function_call, available_functions)
        
        assert result["success"] is False
        assert "requires repository context" in result["error"]

    async def test_execute_function_call_mcp_failure(self, openai_service):
        """Test function execution when MCP call fails."""
        mock_mcp_server = Mock()
        mock_mcp_server.call_tool = AsyncMock(side_effect=Exception("MCP Error"))
        openai_service.set_mcp_server(mock_mcp_server)
        
        function_call = FunctionCall(name="test_function", arguments='{"arg": "value"}')
        available_functions = {}
        
        result = await openai_service.execute_function_call(function_call, available_functions)
        
        assert result["success"] is False
        assert result["error"] == "MCP Error"

    async def test_execute_function_call_no_mcp(self, openai_service):
        """Test function execution without MCP server."""
        function_call = FunctionCall(name="test_function", arguments='{"arg": "value"}')
        available_functions = {}
        
        result = await openai_service.execute_function_call(function_call, available_functions)
        
        assert result["success"] is False
        assert "requires FastMCP server" in result["error"]

    async def test_get_available_functions_with_mcp(self, openai_service):
        """Test getting available functions with MCP server."""
        mock_mcp_server = Mock()
        mock_mcp_server.app = Mock()
        mock_mcp_server.app.get_tools = AsyncMock(return_value={
            "test_tool": Mock(
                description="Test tool description",
                parameters={"type": "object", "properties": {"arg": {"type": "string"}}}
            )
        })
        openai_service.set_mcp_server(mock_mcp_server)
        
        functions = await openai_service.get_available_functions()
        
        assert len(functions) == 1
        assert functions[0].name == "test_tool"
        assert functions[0].description == "Test tool description"

    async def test_get_available_functions_without_mcp(self, openai_service):
        """Test getting available functions without MCP server."""
        functions = await openai_service.get_available_functions()
        
        assert functions == []

    async def test_get_available_functions_mcp_error(self, openai_service):
        """Test getting available functions when MCP fails."""
        mock_mcp_server = Mock()
        mock_mcp_server.app = Mock()
        mock_mcp_server.app.get_tools = AsyncMock(side_effect=Exception("MCP Error"))
        openai_service.set_mcp_server(mock_mcp_server)
        
        functions = await openai_service.get_available_functions()
        
        assert functions == []


class TestOpenAIServiceFormatConversion:
    """Test format conversion helpers."""

    def test_build_conversation_messages_basic(self, openai_service):
        """Test basic conversation message building."""
        messages = openai_service._build_conversation_messages("Test prompt")
        
        assert len(messages) == 1
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == "Test prompt"

    def test_build_conversation_messages_with_system(self, openai_service):
        """Test conversation message building with system prompt."""
        messages = openai_service._build_conversation_messages(
            "User prompt", 
            system_prompt="System instructions"
        )
        
        assert len(messages) == 2
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[0].content == "System instructions"
        assert messages[1].role == MessageRole.USER
        assert messages[1].content == "User prompt"

    def test_build_conversation_messages_with_history(self, openai_service):
        """Test conversation message building with history."""
        history = [
            MessageItem(role=MessageRole.USER, content="Previous question"),
            MessageItem(role=MessageRole.ASSISTANT, content="Previous answer")
        ]
        
        messages = openai_service._build_conversation_messages(
            "Current question",
            conversation_history=history
        )
        
        assert len(messages) == 3
        assert messages[0].content == "Previous question"
        assert messages[1].content == "Previous answer"
        assert messages[2].content == "Current question"

    def test_build_conversation_messages_empty_prompt(self, openai_service):
        """Test conversation message building with empty prompt."""
        messages = openai_service._build_conversation_messages("   ")
        
        assert len(messages) == 0  # Empty prompt should not be added

    def test_convert_messages_to_openai_format(self, openai_service):
        """Test message conversion to OpenAI format."""
        messages = [
            MessageItem(role=MessageRole.SYSTEM, content="System prompt"),
            MessageItem(role=MessageRole.USER, content="User message"),
            MessageItem(role=MessageRole.ASSISTANT, content="Assistant response")
        ]
        
        openai_messages = openai_service._convert_messages_to_openai_format(messages)
        
        assert len(openai_messages) == 3
        assert openai_messages[0]["role"] == "system"
        assert openai_messages[0]["content"] == "System prompt"
        assert openai_messages[1]["role"] == "user"
        assert openai_messages[1]["content"] == "User message"
        assert openai_messages[2]["role"] == "assistant"
        assert openai_messages[2]["content"] == "Assistant response"

    def test_convert_tools_to_openai_format(self, openai_service):
        """Test tool conversion to OpenAI format."""
        tools = [
            FunctionDefinition(
                name="test_function",
                description="Test function",
                parameters={"type": "object", "properties": {"arg": {"type": "string"}}}
            )
        ]
        
        openai_tools = openai_service._convert_tools_to_openai_format(tools)
        
        assert len(openai_tools) == 1
        assert openai_tools[0]["type"] == "function"
        assert openai_tools[0]["function"]["name"] == "test_function"
        assert openai_tools[0]["function"]["description"] == "Test function"

    def test_convert_tool_choice_to_openai_format_string(self, openai_service):
        """Test tool choice conversion from string."""
        result = openai_service._convert_tool_choice_to_openai_format("auto")
        assert result == "auto"

    def test_convert_tool_choice_to_openai_format_enum(self, openai_service):
        """Test tool choice conversion from ToolChoice object."""
        tool_choice = ToolChoice(type="auto")
        result = openai_service._convert_tool_choice_to_openai_format(tool_choice)
        assert result == "auto"

    def test_convert_tool_choice_to_openai_format_function(self, openai_service):
        """Test tool choice conversion for specific function."""
        tool_choice = ToolChoice(type="function", function={"name": "specific_function"})
        result = openai_service._convert_tool_choice_to_openai_format(tool_choice)
        
        assert result["type"] == "function"
        assert result["function"]["name"] == "specific_function"


class TestOpenAIServiceMCPToolConversion:
    """Test MCP tool conversion functionality."""

    def test_convert_mcp_tools_to_function_definitions(self, openai_service):
        """Test converting MCP tools to function definitions."""
        mcp_tools = {
            "tool1": Mock(
                description="First tool",
                parameters={"type": "object", "properties": {"arg1": {"type": "string"}}}
            ),
            "tool2": Mock(
                description="Second tool", 
                parameters={"type": "object", "properties": {"arg2": {"type": "number"}}}
            )
        }
        
        function_defs = openai_service._convert_mcp_tools_to_function_definitions(mcp_tools)
        
        assert len(function_defs) == 2
        assert function_defs[0].name == "tool1"
        assert function_defs[0].description == "First tool"
        assert function_defs[1].name == "tool2"
        assert function_defs[1].description == "Second tool"

    def test_convert_mcp_tools_with_missing_description(self, openai_service):
        """Test converting MCP tools with missing description."""
        mcp_tools = {
            "tool_no_desc": Mock(
                description=None,
                parameters={"type": "object", "properties": {}}
            )
        }
        
        function_defs = openai_service._convert_mcp_tools_to_function_definitions(mcp_tools)
        
        assert len(function_defs) == 1
        assert function_defs[0].name == "tool_no_desc"
        assert function_defs[0].description == "FastMCP tool: tool_no_desc"

    def test_convert_mcp_tools_conversion_error(self, openai_service):
        """Test MCP tool conversion with error."""
        # Create a mock that raises an exception when accessed
        problematic_tool = Mock()
        problematic_tool.description = Mock(side_effect=Exception("Access error"))
        
        mcp_tools = {
            "good_tool": Mock(description="Good tool", parameters={}),
            "bad_tool": problematic_tool
        }
        
        function_defs = openai_service._convert_mcp_tools_to_function_definitions(mcp_tools)
        
        # Should only have the good tool, bad tool should be skipped
        assert len(function_defs) == 1
        assert function_defs[0].name == "good_tool"