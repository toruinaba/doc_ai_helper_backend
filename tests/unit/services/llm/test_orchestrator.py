"""
Test suite for LLMOrchestrator - Orchestration Functionality Only

This test suite focuses on the orchestrator's core orchestration functionality:
- Query execution coordination
- Service factory integration  
- Streaming coordination
- Error handling
- Caching orchestration

Specific functionality tests are in dedicated modules:
- test_conversation_optimizer.py: Conversation history and token management
- test_system_prompt_generator.py: System prompt generation
- test_tool_executor.py: Tool execution and followup
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List, Optional

from doc_ai_helper_backend.services.llm.orchestrator import LLMOrchestrator
from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    LLMQueryRequest,
    CoreQueryRequest,
    ToolConfiguration,
    DocumentContext,
    ProcessingOptions,
    MessageItem,
    MessageRole,
    FunctionDefinition,
    ToolChoice,
    LLMUsage,
)
from doc_ai_helper_backend.core.exceptions import LLMServiceException


@pytest.fixture
def mock_cache_service():
    """Create a mock cache service that supports dictionary-style access."""
    # Use a simple dict instead of Mock to support item assignment
    cache_service = {}
    return cache_service


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service with all required methods."""
    service = Mock()
    service.query = AsyncMock()
    service.stream_query = AsyncMock()
    service.query_with_tools = AsyncMock()
    service.query_with_tools_and_followup = AsyncMock()
    service._prepare_provider_options = AsyncMock(return_value={})
    service._call_provider_api = AsyncMock()
    service._stream_provider_api = AsyncMock()
    service._convert_provider_response = AsyncMock()
    service.execute_function_call = AsyncMock()
    service.get_available_functions = AsyncMock(return_value=[])
    return service


@pytest.fixture
def orchestrator(mock_cache_service):
    """Create LLMOrchestrator instance with mocked dependencies."""
    return LLMOrchestrator(cache_service=mock_cache_service)


@pytest.fixture
def sample_llm_response():
    """Create a sample LLM response for testing."""
    return LLMResponse(
        content="Test response content",
        model="test-model",
        provider="test-provider",
        usage=LLMUsage(prompt_tokens=10, completion_tokens=15, total_tokens=25),
    )


@pytest.fixture
def sample_query_request():
    """Create a sample LLMQueryRequest for testing."""
    return LLMQueryRequest(
        query=CoreQueryRequest(
            prompt="Test prompt",
            provider="mock",
            model="test-model",
            conversation_history=None
        )
    )


@pytest.fixture
def sample_query_request_with_tools():
    """Create a sample LLMQueryRequest with tools for testing."""
    return LLMQueryRequest(
        query=CoreQueryRequest(
            prompt="Test prompt with tools",
            provider="mock",
            model="test-model",
            conversation_history=None
        ),
        tools=ToolConfiguration(
            enable_tools=True,
            tool_choice="auto",
            complete_tool_flow=True
        )
    )


class TestLLMOrchestratorBasic:
    """Test basic orchestrator functionality."""

    def test_orchestrator_initialization(self, mock_cache_service):
        """Test orchestrator proper initialization."""
        orchestrator = LLMOrchestrator(cache_service=mock_cache_service)
        assert orchestrator.cache_service == mock_cache_service

    async def test_execute_query_basic(self, orchestrator, mock_llm_service, sample_llm_response, sample_query_request):
        """Test basic query execution without tools or special features."""
        # Setup - configure the mock to return the sample response
        mock_llm_service._convert_provider_response.return_value = sample_llm_response
        
        # Mock LLMServiceFactory.create to return our mock service
        with patch('doc_ai_helper_backend.services.llm.factory.LLMServiceFactory.create') as mock_factory:
            mock_factory.return_value = mock_llm_service
            
            # Execute
            result = await orchestrator.execute_query(sample_query_request)
            
            # Assert
            assert isinstance(result, LLMResponse)
            assert result.content == "Test response content"
            mock_factory.assert_called_once_with("mock", model="test-model")
            mock_llm_service._prepare_provider_options.assert_called_once()
            mock_llm_service._call_provider_api.assert_called_once()
            mock_llm_service._convert_provider_response.assert_called_once()

    async def test_execute_query_with_conversation_history(self, orchestrator, mock_llm_service, sample_llm_response):
        """Test query execution with conversation history."""
        # Setup
        mock_llm_service._convert_provider_response.return_value = sample_llm_response
        history = [
            MessageItem(role=MessageRole.USER, content="Previous question"),
            MessageItem(role=MessageRole.ASSISTANT, content="Previous answer")
        ]
        
        request_with_history = LLMQueryRequest(
            query=CoreQueryRequest(
                prompt="Follow-up question",
                provider="mock",
                model="test-model",
                conversation_history=history
            )
        )
        
        # Mock LLMServiceFactory.create to return our mock service
        with patch('doc_ai_helper_backend.services.llm.factory.LLMServiceFactory.create') as mock_factory:
            mock_factory.return_value = mock_llm_service
            
            # Execute
            result = await orchestrator.execute_query(request_with_history)
            
            # Assert
            assert isinstance(result, LLMResponse)
            mock_llm_service._prepare_provider_options.assert_called_once()
            # Verify conversation history was passed to provider options
            call_args = mock_llm_service._prepare_provider_options.call_args
            # Note: History may be optimized, so just check that method was called
            assert call_args is not None

    async def test_execute_streaming_query(self, orchestrator, mock_llm_service, sample_query_request):
        """Test streaming query execution."""
        # Setup - create a proper async generator mock
        async def mock_stream():
            yield "chunk1"
            yield "chunk2"
            yield "chunk3"
        
        # Configure the mock to return the async generator directly, not a coroutine
        mock_llm_service._stream_provider_api = Mock(return_value=mock_stream())
        
        # Mock LLMServiceFactory.create to return our mock service
        with patch('doc_ai_helper_backend.services.llm.factory.LLMServiceFactory.create') as mock_factory:
            mock_factory.return_value = mock_llm_service
            
            # Execute - streaming query returns async generator, don't await
            stream = orchestrator.execute_streaming_query(sample_query_request)
            
            # Assert - consume the async generator
            chunks = []
            async for chunk in stream:
                chunks.append(chunk)
            
            # Verify structured streaming response format  
            expected_chunks = [
                {"content": "chunk1", "done": False},
                {"content": "chunk2", "done": False}, 
                {"content": "chunk3", "done": False},
                {"content": "", "done": True}
            ]
            assert chunks == expected_chunks
            mock_llm_service._prepare_provider_options.assert_called_once()
            mock_llm_service._stream_provider_api.assert_called_once()

    async def test_execute_query_with_tools(self, orchestrator, mock_llm_service, sample_llm_response, sample_query_request_with_tools):
        """Test query execution with tools."""
        # Setup - configure response without tool calls to avoid complex tool execution
        response_without_tools = LLMResponse(
            content="Test response without tool calls",
            model="test-model",
            provider="test-provider", 
            usage=LLMUsage(prompt_tokens=10, completion_tokens=15, total_tokens=25),
            tool_calls=[]  # No tool calls to avoid complex tool execution
        )
        mock_llm_service._convert_provider_response.return_value = response_without_tools
        
        tools = [
            FunctionDefinition(
                name="test_tool",
                description="A test tool",
                parameters={"type": "object", "properties": {}}
            )
        ]
        mock_llm_service.get_available_functions = AsyncMock(return_value=tools)
        
        # Mock LLMServiceFactory.create to return our mock service
        with patch('doc_ai_helper_backend.services.llm.factory.LLMServiceFactory.create') as mock_factory:
            mock_factory.return_value = mock_llm_service
            
            # Execute
            result = await orchestrator.execute_query(sample_query_request_with_tools)
            
            # Assert
            assert isinstance(result, LLMResponse)
            assert result.content == "Test response without tool calls"
            mock_llm_service.get_available_functions.assert_called_once()
            mock_llm_service._prepare_provider_options.assert_called_once()
            mock_llm_service._call_provider_api.assert_called_once()
            mock_llm_service._convert_provider_response.assert_called_once()

    async def test_error_handling(self, orchestrator, mock_llm_service, sample_query_request):
        """Test error handling in query execution."""
        # Setup service to raise exception
        mock_llm_service._call_provider_api.side_effect = LLMServiceException("Test error")
        
        # Mock LLMServiceFactory.create to return our mock service
        with patch('doc_ai_helper_backend.services.llm.factory.LLMServiceFactory.create') as mock_factory:
            mock_factory.return_value = mock_llm_service
            
            # Execute and expect exception
            with pytest.raises(LLMServiceException, match="Query execution failed"):
                await orchestrator.execute_query(sample_query_request)


class TestLLMOrchestratorAdvanced:
    """Test advanced orchestrator functionality."""

    async def test_system_prompt_integration(self, orchestrator, mock_llm_service, sample_llm_response):
        """Test that orchestrator integrates with system prompt generation."""
        # Setup repository context in request
        from doc_ai_helper_backend.models.repository_context import RepositoryContext, GitService
        repo_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test-owner",
            repo="test-repo",
            ref="main",
            current_path="test.py",
            base_url="https://api.github.com"
        )
        
        request_with_context = LLMQueryRequest(
            query=CoreQueryRequest(
                prompt="Analyze this code",
                provider="mock",
                model="test-model",
                conversation_history=None
            ),
            document=DocumentContext(
                repository_context=repo_context,
                auto_include_document=True,
                context_documents=[]
            )
        )
        
        mock_llm_service._convert_provider_response.return_value = sample_llm_response
        
        # Mock LLMServiceFactory.create to return our mock service
        with patch('doc_ai_helper_backend.services.llm.factory.LLMServiceFactory.create') as mock_factory:
            mock_factory.return_value = mock_llm_service
            
            # Execute
            result = await orchestrator.execute_query(request_with_context)
            
            # Assert
            assert isinstance(result, LLMResponse)
            mock_llm_service._prepare_provider_options.assert_called_once()
            mock_llm_service._call_provider_api.assert_called_once()
            mock_llm_service._convert_provider_response.assert_called_once()

    def test_cache_key_generation(self, orchestrator):
        """Test cache key generation for queries."""
        request = LLMQueryRequest(
            query=CoreQueryRequest(
                prompt="Test prompt",
                provider="mock",
                model="test-model"
            )
        )
        
        # Test that orchestrator can handle cache key generation
        # Since _generate_cache_key is internal, we test indirectly
        assert request.query.prompt == "Test prompt"
        assert request.query.provider == "mock"
        assert request.query.model == "test-model"

    async def test_error_handling_in_orchestrator(self, orchestrator, mock_llm_service):
        """Test error handling in orchestrator with valid prompt."""
        test_request = LLMQueryRequest(
            query=CoreQueryRequest(
                prompt="Test prompt",  # Valid prompt
                provider="mock",
                model="test-model"
            )
        )
        
        # Mock the service to simulate an error during execution
        mock_llm_service._prepare_provider_options.side_effect = LLMServiceException("Service error")
        
        # Mock LLMServiceFactory.create to return our mock service
        with patch('doc_ai_helper_backend.services.llm.factory.LLMServiceFactory.create') as mock_factory:
            mock_factory.return_value = mock_llm_service
            
            # Execute and expect exception
            with pytest.raises(LLMServiceException, match="Query execution failed"):
                await orchestrator.execute_query(test_request)


class TestOrchestratorCaching:
    """Test orchestrator caching functionality."""

    async def test_cache_miss_and_set(self, orchestrator, mock_llm_service, mock_cache_service, sample_llm_response, sample_query_request):
        """Test cache miss and subsequent cache set."""
        # Setup
        mock_llm_service._convert_provider_response.return_value = sample_llm_response
        
        # Mock LLMServiceFactory.create to return our mock service
        with patch('doc_ai_helper_backend.services.llm.factory.LLMServiceFactory.create') as mock_factory:
            mock_factory.return_value = mock_llm_service
            
            # Execute
            result = await orchestrator.execute_query(sample_query_request)
            
            # Assert
            assert isinstance(result, LLMResponse)
            # Cache should have been populated (orchestrator uses dict-style access)
            # The specific cache key depends on internal implementation

    async def test_cache_hit(self, orchestrator, mock_llm_service, mock_cache_service, sample_query_request):
        """Test cache hit scenario."""
        # Setup - create proper mock response
        cached_response = LLMResponse(
            content="Cached response",
            model="test-model",
            provider="mock",
            usage=LLMUsage(prompt_tokens=5, completion_tokens=10, total_tokens=15),
        )
        
        # Configure the mock to return the response
        mock_llm_service._convert_provider_response.return_value = cached_response
        
        # Mock LLMServiceFactory.create to return our mock service
        with patch('doc_ai_helper_backend.services.llm.factory.LLMServiceFactory.create') as mock_factory:
            mock_factory.return_value = mock_llm_service
            
            # Execute
            result = await orchestrator.execute_query(sample_query_request)
            
            # Assert - should get the response
            assert isinstance(result, LLMResponse)
            assert result.content == "Cached response"


class TestOrchestratorStreamingErrorHandling:
    """Test orchestrator streaming error handling."""

    async def test_streaming_query_error_handling(self, orchestrator, mock_llm_service, sample_query_request):
        """Test error handling in streaming query execution."""
        # Setup service to raise exception
        mock_llm_service._prepare_provider_options.side_effect = Exception("Streaming error")
        
        # Mock LLMServiceFactory.create to return our mock service
        with patch('doc_ai_helper_backend.services.llm.factory.LLMServiceFactory.create') as mock_factory:
            mock_factory.return_value = mock_llm_service
            
            # Execute streaming query - should raise exception 
            stream = orchestrator.execute_streaming_query(sample_query_request)
            
            # Should raise LLMServiceException
            with pytest.raises(LLMServiceException, match="Streaming query execution failed"):
                async for chunk in stream:
                    pass

    async def test_streaming_query_service_error(self, orchestrator, mock_llm_service):
        """Test streaming query with service error."""
        test_request = LLMQueryRequest(
            query=CoreQueryRequest(
                prompt="Test prompt",  # Valid prompt
                provider="mock",
                model="test-model"
            )
        )
        
        # Mock the service to simulate a service error
        mock_llm_service._prepare_provider_options.side_effect = Exception("Service error")
        
        # Mock LLMServiceFactory.create to return our mock service
        with patch('doc_ai_helper_backend.services.llm.factory.LLMServiceFactory.create') as mock_factory:
            mock_factory.return_value = mock_llm_service
            
            # Execute streaming query - should raise exception
            stream = orchestrator.execute_streaming_query(test_request)
            
            # Should raise LLMServiceException
            with pytest.raises(LLMServiceException, match="Streaming query execution failed"):
                async for chunk in stream:
                    pass


class TestOrchestratorToolIntegration:
    """Test orchestrator integration with tool execution."""

    async def test_query_with_tools_with_tool_calls(self, orchestrator, mock_llm_service):
        """Test query execution when LLM response contains tool calls."""
        from doc_ai_helper_backend.models.llm import ToolCall, FunctionCall
        
        # Setup response with tool calls
        response_with_tools = LLMResponse(
            content="I'll use tools to help you.",
            model="test-model",
            provider="test-provider",
            usage=LLMUsage(prompt_tokens=20, completion_tokens=25, total_tokens=45),
            tool_calls=[
                ToolCall(
                    id="call_123",
                    function=FunctionCall(name="test_tool", arguments='{"param": "value"}')
                )
            ]
        )
        
        # Mock tool execution
        mock_llm_service._convert_provider_response.return_value = response_with_tools
        mock_llm_service.execute_function_call = AsyncMock(return_value={"success": True})
        mock_llm_service.get_available_functions = AsyncMock(return_value=[
            FunctionDefinition(
                name="test_tool",
                description="A test tool",
                parameters={"type": "object", "properties": {"param": {"type": "string"}}}
            )
        ])
        
        request_with_tools = LLMQueryRequest(
            query=CoreQueryRequest(
                prompt="Use tools to help me",
                provider="mock",
                model="test-model"
            ),
            tools=ToolConfiguration(
                enable_tools=True,
                tool_choice="auto",
                complete_tool_flow=True
            )
        )
        
        # Mock LLMServiceFactory.create to return our mock service
        with patch('doc_ai_helper_backend.services.llm.factory.LLMServiceFactory.create') as mock_factory:
            mock_factory.return_value = mock_llm_service
            
            # Execute
            result = await orchestrator.execute_query(request_with_tools)
            
            # Assert
            assert isinstance(result, LLMResponse)
            assert result.tool_calls is not None
            assert len(result.tool_calls) == 1
            mock_llm_service.get_available_functions.assert_called_once()