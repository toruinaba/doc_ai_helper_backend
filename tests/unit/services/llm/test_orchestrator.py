"""
Test suite for LLMOrchestrator - New Architecture (Fixed)

This test suite is designed for the new refactored LLM architecture
focusing on the orchestrator's core functionality with proper mocking.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List, Optional

from doc_ai_helper_backend.services.llm.orchestrator import LLMOrchestrator, _estimate_message_tokens, _optimize_conversation_history
from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    MessageItem,
    MessageRole,
    FunctionDefinition,
    ToolChoice,
    LLMUsage,
)
from doc_ai_helper_backend.core.exceptions import LLMServiceException


@pytest.fixture
def mock_cache_service():
    """Create a mock cache service that always misses cache."""
    cache_service = Mock()
    cache_service.get = Mock(return_value=None)  # Sync call - Always cache miss
    cache_service.set = Mock(return_value=None)  # Sync call
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


class TestLLMOrchestratorBasic:
    """Test basic orchestrator functionality."""

    def test_orchestrator_initialization(self, mock_cache_service):
        """Test orchestrator proper initialization."""
        orchestrator = LLMOrchestrator(cache_service=mock_cache_service)
        assert orchestrator.cache_service == mock_cache_service

    async def test_execute_query_basic(self, orchestrator, mock_llm_service, sample_llm_response):
        """Test basic query execution without tools or special features."""
        # Setup - configure the mock to return the sample response
        mock_llm_service._convert_provider_response.return_value = sample_llm_response
        
        # Execute
        result = await orchestrator.execute_query(
            service=mock_llm_service,
            prompt="Test prompt",
            conversation_history=None,
            options=None,
            repository_context=None,
            document_metadata=None,
            document_content=None,
            include_document_in_system_prompt=True
        )
        
        # Assert
        assert isinstance(result, LLMResponse)
        assert result.content == "Test response content"
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
        
        # Execute
        result = await orchestrator.execute_query(
            service=mock_llm_service,
            prompt="Follow-up question",
            conversation_history=history,
            options=None,
            repository_context=None,
            document_metadata=None,
            document_content=None,
            include_document_in_system_prompt=True
        )
        
        # Assert
        assert isinstance(result, LLMResponse)
        mock_llm_service._prepare_provider_options.assert_called_once()
        # Verify conversation history was passed to provider options
        call_args = mock_llm_service._prepare_provider_options.call_args
        assert call_args.kwargs["conversation_history"] == history

    async def test_execute_streaming_query(self, orchestrator, mock_llm_service):
        """Test streaming query execution."""
        # Setup - create a proper async generator mock
        async def mock_stream():
            yield "chunk1"
            yield "chunk2"
            yield "chunk3"
        
        # Configure the mock to return the async generator directly, not a coroutine
        mock_llm_service._stream_provider_api = Mock(return_value=mock_stream())
        
        # Execute - streaming query returns async generator, don't await
        stream = orchestrator.execute_streaming_query(
            service=mock_llm_service,
            prompt="Test streaming prompt",
            conversation_history=None,
            options=None,
            repository_context=None,
            document_metadata=None,
            document_content=None,
            include_document_in_system_prompt=True
        )
        
        # Assert - consume the async generator
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        
        assert chunks == ["chunk1", "chunk2", "chunk3"]
        mock_llm_service._prepare_provider_options.assert_called_once()
        mock_llm_service._stream_provider_api.assert_called_once()

    async def test_execute_query_with_tools(self, orchestrator, mock_llm_service, sample_llm_response):
        """Test query execution with tools."""
        # Setup - configure response without tool calls
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
        
        # Execute
        result = await orchestrator.execute_query_with_tools(
            service=mock_llm_service,
            prompt="Test prompt with tools",
            tools=tools,
            conversation_history=None,
            tool_choice=None,
            options=None,
            repository_context=None,
            document_metadata=None,
            document_content=None
        )
        
        # Assert
        assert isinstance(result, LLMResponse)
        assert result.content == "Test response without tool calls"
        mock_llm_service._prepare_provider_options.assert_called_once()
        mock_llm_service._call_provider_api.assert_called_once()
        mock_llm_service._convert_provider_response.assert_called_once()

    async def test_error_handling(self, orchestrator, mock_llm_service):
        """Test error handling in query execution."""
        # Setup service to raise exception
        mock_llm_service._call_provider_api.side_effect = LLMServiceException("Test error")
        
        # Execute and expect exception
        with pytest.raises(LLMServiceException, match="Query execution failed"):
            await orchestrator.execute_query(
                service=mock_llm_service,
                prompt="Error prompt",
                conversation_history=None,
                options=None,
                repository_context=None,
                document_metadata=None,
                document_content=None,
                include_document_in_system_prompt=True
            )


class TestLLMOrchestratorAdvanced:
    """Test advanced orchestrator functionality."""

    async def test_system_prompt_generation(self, orchestrator, mock_llm_service, sample_llm_response):
        """Test system prompt generation with repository context."""
        # Setup mock repository context
        mock_repo_context = Mock()
        mock_repo_context.repository_name = "test-repo"
        mock_repo_context.current_file_path = "test.py"
        mock_repo_context.repository_description = "Test repository"
        
        mock_llm_service._convert_provider_response.return_value = sample_llm_response
        
        # Execute
        result = await orchestrator.execute_query(
            service=mock_llm_service,
            prompt="Analyze this code",
            conversation_history=None,
            options=None,
            repository_context=mock_repo_context,
            document_metadata=None,
            document_content=None,
            include_document_in_system_prompt=True
        )
        
        # Assert
        assert isinstance(result, LLMResponse)
        mock_llm_service._prepare_provider_options.assert_called_once()
        mock_llm_service._call_provider_api.assert_called_once()
        mock_llm_service._convert_provider_response.assert_called_once()

    def test_system_prompt_without_context(self, orchestrator):
        """Test system prompt generation without context."""
        result = orchestrator._generate_system_prompt(
            repository_context=None,
            document_metadata=None,
            document_content=None,
            include_document_in_system_prompt=False
        )
        assert result is None

    def test_build_conversation_messages(self, orchestrator):
        """Test conversation message building."""
        history = [
            MessageItem(role=MessageRole.USER, content="Previous question"),
            MessageItem(role=MessageRole.ASSISTANT, content="Previous answer")
        ]
        
        messages = orchestrator.build_conversation_messages(
            prompt="Current question",
            conversation_history=history,
            system_prompt="System instructions"
        )
        
        assert len(messages) == 4  # system + history + current
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[0].content == "System instructions"
        assert messages[1].role == MessageRole.USER
        assert messages[1].content == "Previous question"
        assert messages[2].role == MessageRole.ASSISTANT
        assert messages[2].content == "Previous answer"
        assert messages[3].role == MessageRole.USER
        assert messages[3].content == "Current question"

    def test_cache_key_generation(self, orchestrator):
        """Test cache key generation."""
        history = [MessageItem(role=MessageRole.USER, content="Test")]
        
        key1 = orchestrator._generate_cache_key(
            prompt="Test prompt",
            conversation_history=history,
            options={"temp": 0.5},
            repository_context=None,
            document_metadata=None,
            document_content="Test content"
        )
        
        key2 = orchestrator._generate_cache_key(  
            prompt="Test prompt",
            conversation_history=history,
            options={"temp": 0.5},
            repository_context=None,
            document_metadata=None,
            document_content="Test content"
        )
        
        # Same inputs should generate same key
        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 32  # MD5 hex length

    async def test_empty_prompt_validation(self, orchestrator, mock_llm_service):
        """Test empty prompt validation."""
        with pytest.raises(LLMServiceException, match="Prompt cannot be empty"):
            await orchestrator.execute_query(
                service=mock_llm_service,
                prompt="",  # Empty prompt
                conversation_history=None,
                options=None,
                repository_context=None,
                document_metadata=None,
                document_content=None,
                include_document_in_system_prompt=True
            )


class TestConversationHistoryOptimization:
    """Test conversation history optimization functions."""

    def test_estimate_message_tokens_basic(self):
        """Test basic token estimation."""
        message = MessageItem(role=MessageRole.USER, content="Hello world")
        tokens = _estimate_message_tokens(message)
        assert isinstance(tokens, int)
        assert tokens > 0

    def test_estimate_message_tokens_long_content(self):
        """Test token estimation with long content."""
        long_content = "This is a very long message " * 20
        message = MessageItem(role=MessageRole.USER, content=long_content)
        tokens = _estimate_message_tokens(message)
        assert isinstance(tokens, int)
        assert tokens > 50  # Should be significantly more than short message

    def test_estimate_message_tokens_fallback(self):
        """Test token estimation fallback when tiktoken is not available."""
        # Mock tiktoken import to raise ImportError
        with patch.dict('sys.modules', {'tiktoken': None}):
            # Reload the function to trigger ImportError path
            import importlib
            import doc_ai_helper_backend.services.llm.orchestrator as orch_module
            importlib.reload(orch_module)
            
            message = MessageItem(role=MessageRole.USER, content="Test message for fallback")
            tokens = orch_module._estimate_message_tokens(message)
            
            # Should fall back to character/4 approximation
            assert isinstance(tokens, int)
            assert tokens > 0
            # Should be approximately len(content) // 4 plus role text
            assert tokens >= 5  # At least some tokens for the message

    def test_optimize_conversation_history_basic(self):
        """Test conversation history optimization."""
        history = [
            MessageItem(role=MessageRole.USER, content="Question 1"),
            MessageItem(role=MessageRole.ASSISTANT, content="Answer 1"),
            MessageItem(role=MessageRole.USER, content="Question 2"),
            MessageItem(role=MessageRole.ASSISTANT, content="Answer 2"),
        ]
        
        optimized, info = _optimize_conversation_history(history, max_tokens=1000)
        
        assert isinstance(optimized, list)
        assert isinstance(info, dict)
        assert "was_optimized" in info
        assert "original_messages" in info
        assert "final_messages" in info

    def test_optimize_conversation_history_empty(self):
        """Test optimization with empty history."""
        optimized, info = _optimize_conversation_history([], max_tokens=1000)
        
        assert optimized == []
        assert info["was_optimized"] is False
        assert "original_messages" not in info  # Empty history doesn't have these keys
        assert "final_messages" not in info

    def test_optimize_conversation_history_large(self):
        """Test optimization with large history that needs truncation."""
        # Create a large history that should trigger optimization
        large_history = []
        for i in range(50):
            large_history.extend([
                MessageItem(role=MessageRole.USER, content=f"Long question {i} " * 20),
                MessageItem(role=MessageRole.ASSISTANT, content=f"Long answer {i} " * 20),
            ])
        
        optimized, info = _optimize_conversation_history(large_history, max_tokens=500)
        
        assert len(optimized) <= len(large_history)
        assert info["was_optimized"] is True
        assert info["final_messages"] < info["original_messages"]


class TestOrchestratorCaching:
    """Test caching functionality - pure unit test level."""

    async def test_cache_miss_and_set(self, orchestrator, mock_llm_service, mock_cache_service, sample_llm_response):
        """Test cache miss scenario and cache setting."""
        # Setup - cache miss
        mock_cache_service.get.return_value = None
        mock_llm_service._convert_provider_response.return_value = sample_llm_response
        
        # Execute
        result = await orchestrator.execute_query(
            service=mock_llm_service,
            prompt="Cacheable prompt",
            conversation_history=None,
            options=None,
            repository_context=None,
            document_metadata=None,
            document_content=None,
            include_document_in_system_prompt=True
        )
        
        # Assert
        assert isinstance(result, LLMResponse)
        # Cache should be checked and result should be stored
        mock_cache_service.get.assert_called()
        mock_cache_service.set.assert_called()

    async def test_cache_hit(self, orchestrator, mock_llm_service, mock_cache_service):
        """Test cache hit scenario."""
        # Setup - cache hit
        cached_response = LLMResponse(
            content="Cached response content",
            model="cached-model",
            provider="cached-provider",
            usage=LLMUsage(prompt_tokens=5, completion_tokens=10, total_tokens=15),
        )
        mock_cache_service.get.return_value = cached_response
        
        # Execute
        result = await orchestrator.execute_query(
            service=mock_llm_service,
            prompt="Cached prompt",
            conversation_history=None,
            options=None,
            repository_context=None,
            document_metadata=None,
            document_content=None,
            include_document_in_system_prompt=True
        )
        
        # Assert
        assert isinstance(result, LLMResponse)
        assert result.content == "Cached response content"
        # LLM service should not be called when cache hits
        mock_llm_service._prepare_provider_options.assert_not_called()
        mock_llm_service._call_provider_api.assert_not_called()


class TestOrchestratorUtilities:
    """Test orchestrator utility methods - pure unit test level."""

    def test_conversation_optimization_info_setting(self, orchestrator, sample_llm_response):
        """Test conversation optimization info setting."""
        history = [
            MessageItem(role=MessageRole.USER, content="Test question"),
            MessageItem(role=MessageRole.ASSISTANT, content="Test answer")
        ]
        
        # Call the private method directly
        orchestrator._set_conversation_optimization_info(sample_llm_response, history)
        
        # Assert optimization info was set
        assert hasattr(sample_llm_response, 'optimized_conversation_history')
        assert hasattr(sample_llm_response, 'history_optimization_info')
        assert isinstance(sample_llm_response.history_optimization_info, dict)
        assert 'was_optimized' in sample_llm_response.history_optimization_info

    def test_conversation_optimization_info_no_history(self, orchestrator, sample_llm_response):
        """Test conversation optimization info with no history."""
        orchestrator._set_conversation_optimization_info(sample_llm_response, None)
        
        assert sample_llm_response.optimized_conversation_history == []
        assert sample_llm_response.history_optimization_info['was_optimized'] is False
        assert sample_llm_response.history_optimization_info['reason'] == "No conversation history provided"

    def test_system_prompt_with_document_metadata(self, orchestrator):
        """Test system prompt generation with document metadata."""
        from unittest.mock import Mock
        
        # Mock document metadata
        mock_doc_metadata = Mock()
        mock_doc_metadata.is_documentation = True
        mock_doc_metadata.is_code_file = False
        
        result = orchestrator._generate_system_prompt(
            repository_context=None,
            document_metadata=mock_doc_metadata,
            document_content=None,
            include_document_in_system_prompt=True
        )
        
        assert result is not None
        assert "このファイルはドキュメントファイルです。" in result

    def test_system_prompt_with_code_metadata(self, orchestrator):
        """Test system prompt generation with code file metadata."""
        from unittest.mock import Mock
        
        # Mock code file metadata  
        mock_doc_metadata = Mock()
        mock_doc_metadata.is_documentation = False
        mock_doc_metadata.is_code_file = True
        
        result = orchestrator._generate_system_prompt(
            repository_context=None,
            document_metadata=mock_doc_metadata,
            document_content=None,
            include_document_in_system_prompt=True
        )
        
        assert result is not None
        assert "このファイルはコードファイルです。" in result

    def test_system_prompt_with_repository_context(self, orchestrator):
        """Test system prompt generation with repository context."""
        from unittest.mock import Mock
        
        # Mock repository context
        mock_repo_context = Mock()
        mock_repo_context.owner = "test-owner"
        mock_repo_context.repo = "test-repo"
        mock_repo_context.current_path = "src/main.py"
        
        result = orchestrator._generate_system_prompt(
            repository_context=mock_repo_context,
            document_metadata=None,
            document_content=None,
            include_document_in_system_prompt=True
        )
        
        assert result is not None
        assert "リポジトリ: test-owner/test-repo" in result
        assert "現在のファイル: src/main.py" in result

    async def test_streaming_query_error_handling(self, orchestrator, mock_llm_service):
        """Test streaming query error handling."""
        # Setup service to raise exception in streaming
        mock_llm_service._prepare_provider_options.side_effect = LLMServiceException("Stream error")
        
        # Execute and expect exception
        with pytest.raises(LLMServiceException, match="Streaming query execution failed"):
            stream = orchestrator.execute_streaming_query(
                service=mock_llm_service,
                prompt="Stream error prompt",
                conversation_history=None,
                options=None,
                repository_context=None,
                document_metadata=None,
                document_content=None,
                include_document_in_system_prompt=True
            )
            # Consume the generator to trigger the error
            async for chunk in stream:
                pass

    async def test_streaming_query_empty_prompt_validation(self, orchestrator, mock_llm_service):
        """Test streaming query empty prompt validation."""
        with pytest.raises(LLMServiceException, match="Prompt cannot be empty"):
            stream = orchestrator.execute_streaming_query(
                service=mock_llm_service,
                prompt="   ",  # Whitespace only prompt
                conversation_history=None,
                options=None,
                repository_context=None,
                document_metadata=None,
                document_content=None,
                include_document_in_system_prompt=True
            )
            # Try to consume the generator
            async for chunk in stream:
                pass

    def test_system_prompt_generation_comprehensive(self, orchestrator):
        """Test comprehensive system prompt generation scenarios."""
        from unittest.mock import Mock
        
        # Test with complete context
        mock_repo_context = Mock()
        mock_repo_context.owner = "test-owner"
        mock_repo_context.repo = "test-repo"
        mock_repo_context.current_path = "src/main.py"
        
        mock_doc_metadata = Mock()
        mock_doc_metadata.is_documentation = True
        mock_doc_metadata.is_code_file = False
        
        result = orchestrator._generate_system_prompt(
            repository_context=mock_repo_context,
            document_metadata=mock_doc_metadata,
            document_content="Sample content",
            include_document_in_system_prompt=True
        )
        
        assert result is not None
        assert "=== BILINGUAL TOOL EXECUTION SYSTEM ===" in result
        assert "リポジトリ: test-owner/test-repo" in result
        assert "現在のファイル: src/main.py" in result
        assert "このファイルはドキュメントファイルです。" in result

    async def test_query_with_tools_with_tool_calls(self, orchestrator, mock_llm_service):
        """Test query with tools when tool calls are returned."""
        from doc_ai_helper_backend.models.llm import ToolCall, FunctionCall
        
        # Create a response WITH tool calls
        tool_call = ToolCall(
            id="test-call-1",
            function=FunctionCall(
                name="test_function",
                arguments='{"arg1": "value1"}'
            )
        )
        
        response_with_tools = LLMResponse(
            content="I'll use a tool to help you",
            model="test-model",
            provider="test-provider",
            usage=LLMUsage(prompt_tokens=10, completion_tokens=15, total_tokens=25),
            tool_calls=[tool_call]
        )
        
        mock_llm_service._convert_provider_response.return_value = response_with_tools
        mock_llm_service.execute_function_call.return_value = {"success": True, "result": "Tool executed successfully"}
        
        tools = [
            FunctionDefinition(
                name="test_function",
                description="A test function",
                parameters={"type": "object", "properties": {"arg1": {"type": "string"}}}
            )
        ]
        
        # Mock repository context for tool execution
        mock_repo_context = Mock()
        mock_repo_context.service = "github"
        mock_repo_context.owner = "test-owner"
        mock_repo_context.repo = "test-repo"
        mock_repo_context.ref = "main"
        mock_repo_context.current_path = "test.py"
        mock_repo_context.base_url = "https://api.github.com"
        
        # Execute
        result = await orchestrator.execute_query_with_tools(
            service=mock_llm_service,
            prompt="Test prompt with tool execution",
            tools=tools,
            conversation_history=None,
            tool_choice=None,
            options=None,
            repository_context=mock_repo_context,
            document_metadata=None,
            document_content=None
        )
        
        # Assert
        assert isinstance(result, LLMResponse)
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        mock_llm_service.execute_function_call.assert_called_once()

    def test_convert_repository_context_to_dict(self, orchestrator):
        """Test repository context conversion to dict."""
        mock_repo_context = Mock()
        mock_repo_context.service = Mock()
        mock_repo_context.service.value = "github"  # Enum with value
        mock_repo_context.owner = "test-owner"
        mock_repo_context.repo = "test-repo"
        mock_repo_context.ref = "main"
        mock_repo_context.current_path = "test.py"
        mock_repo_context.base_url = "https://api.github.com"
        
        result = orchestrator._convert_repository_context_to_dict(mock_repo_context)
        
        assert result is not None
        assert result["service"] == "github"
        assert result["owner"] == "test-owner"
        assert result["repo"] == "test-repo"
        assert result["ref"] == "main"
        assert result["current_path"] == "test.py"
        assert result["base_url"] == "https://api.github.com"

    def test_convert_repository_context_to_dict_none(self, orchestrator):
        """Test repository context conversion when context is None."""
        result = orchestrator._convert_repository_context_to_dict(None)
        assert result is None