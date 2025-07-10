"""
Tests for the QueryManager utility class.

This module tests the QueryManager class which manages the complete
workflow of LLM queries including caching, system prompt generation, and response processing.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from doc_ai_helper_backend.services.llm.query_manager import (
    QueryManager,
)
from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    LLMUsage,
    MessageItem,
    MessageRole,
)
from doc_ai_helper_backend.core.exceptions import LLMServiceException


@pytest.fixture
def mock_cache_service():
    """Mock cache service for testing."""
    return MagicMock()


@pytest.fixture
def mock_system_prompt_builder():
    """Mock system prompt builder for testing."""
    mock_builder = MagicMock()
    mock_builder.build_system_prompt = MagicMock(return_value="System prompt")
    return mock_builder


@pytest.fixture
def query_orchestrator(mock_cache_service, mock_system_prompt_builder):
    """Query orchestrator instance for testing."""
    return QueryManager(
        cache_service=mock_cache_service,
        system_prompt_builder=mock_system_prompt_builder,
    )


@pytest.fixture
def mock_service():
    """Mock LLM service for testing."""
    mock = MagicMock()
    mock._prepare_provider_options = AsyncMock(return_value={"model": "test-model"})
    mock._call_provider_api = AsyncMock(return_value={"content": "Test response"})
    mock._convert_provider_response = AsyncMock(
        return_value=LLMResponse(
            content="Test response",
            model="test-model",
            provider="test",
            usage=LLMUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            raw_response={"content": "Test response"},
        )
    )
    mock._stream_provider_api = AsyncMock()
    return mock


class TestQueryManager:
    """Test cases for the QueryManager class."""

    @pytest.mark.asyncio
    async def test_orchestrate_query_basic(
        self, query_orchestrator, mock_service, mock_cache_service
    ):
        """Test basic query orchestration."""
        # Setup cache miss
        mock_cache_service.get.return_value = None

        result = await query_orchestrator.orchestrate_query(
            service=mock_service,
            prompt="Test prompt",
        )

        assert result.content == "Test response"
        assert result.model == "test-model"

        # Verify cache operations
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_orchestrate_query_cache_hit(
        self, query_orchestrator, mock_service, mock_cache_service
    ):
        """Test query orchestration with cache hit."""
        cached_response = LLMResponse(
            content="Cached response",
            model="cached-model",
            provider="cache",
            usage=LLMUsage(prompt_tokens=5, completion_tokens=10, total_tokens=15),
            raw_response={"content": "Cached response"},
        )
        mock_cache_service.get.return_value = cached_response

        result = await query_orchestrator.orchestrate_query(
            service=mock_service,
            prompt="Test prompt",
        )

        assert result.content == "Cached response"
        assert result.model == "cached-model"

        # Verify cache hit behavior
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_not_called()

        # Verify service methods were not called
        mock_service._call_provider_api.assert_not_called()

    @pytest.mark.asyncio
    async def test_orchestrate_query_empty_prompt(
        self, query_orchestrator, mock_service
    ):
        """Test query orchestration with empty prompt."""
        with pytest.raises(LLMServiceException) as exc_info:
            await query_orchestrator.orchestrate_query(
                service=mock_service,
                prompt="",
            )

        assert "Prompt cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_orchestrate_query_with_conversation_history(
        self, query_orchestrator, mock_service, mock_cache_service
    ):
        """Test query orchestration with conversation history."""
        mock_cache_service.get.return_value = None

        conversation_history = [
            MessageItem(role=MessageRole.USER, content="Previous question"),
            MessageItem(role=MessageRole.ASSISTANT, content="Previous answer"),
        ]

        result = await query_orchestrator.orchestrate_query(
            service=mock_service,
            prompt="Follow-up question",
            conversation_history=conversation_history,
        )

        assert result.content == "Test response"

        # Verify service was called with options
        mock_service._prepare_provider_options.assert_called_once()

    @pytest.mark.asyncio
    async def test_orchestrate_streaming_query(self, query_orchestrator, mock_service):
        """Test streaming query orchestration."""

        # Setup streaming response as an async generator
        async def mock_stream(options):
            yield "chunk1"
            yield "chunk2"
            yield "chunk3"

        # Mock the stream method to return an async generator directly
        mock_service._stream_provider_api = mock_stream

        chunks = []
        async for chunk in query_orchestrator.orchestrate_streaming_query(
            service=mock_service,
            prompt="Test streaming prompt",
        ):
            chunks.append(chunk)

        assert chunks == ["chunk1", "chunk2", "chunk3"]

    @pytest.mark.asyncio
    async def test_orchestrate_query_with_tools(
        self, query_orchestrator, mock_service, mock_cache_service
    ):
        """Test query orchestration with tools."""
        from doc_ai_helper_backend.models.llm import FunctionDefinition

        mock_cache_service.get.return_value = None

        tools = [
            FunctionDefinition(
                name="test_function",
                description="Test function",
                parameters={
                    "type": "object",
                    "properties": {"arg": {"type": "string"}},
                    "required": ["arg"],
                },
            )
        ]

        result = await query_orchestrator.orchestrate_query_with_tools(
            service=mock_service,
            prompt="Use tools",
            tools=tools,
        )

        assert result.content == "Test response"
        mock_service._prepare_provider_options.assert_called_once()

    def test_build_conversation_messages_basic(self, query_orchestrator):
        """Test building conversation messages."""
        messages = query_orchestrator.build_conversation_messages(prompt="Test prompt")

        assert len(messages) == 1
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == "Test prompt"

    def test_build_conversation_messages_with_system_prompt(self, query_orchestrator):
        """Test building conversation messages with system prompt."""
        messages = query_orchestrator.build_conversation_messages(
            prompt="Test prompt", system_prompt="System instruction"
        )

        assert len(messages) == 2
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[0].content == "System instruction"
        assert messages[1].role == MessageRole.USER
        assert messages[1].content == "Test prompt"

    def test_build_conversation_messages_with_history(self, query_orchestrator):
        """Test building conversation messages with history."""
        history = [
            MessageItem(role=MessageRole.USER, content="Previous question"),
            MessageItem(role=MessageRole.ASSISTANT, content="Previous answer"),
        ]

        messages = query_orchestrator.build_conversation_messages(
            prompt="Follow-up question",
            conversation_history=history,
            system_prompt="System instruction",
        )

        assert len(messages) == 4
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[1].role == MessageRole.USER
        assert messages[1].content == "Previous question"
        assert messages[2].role == MessageRole.ASSISTANT
        assert messages[2].content == "Previous answer"
        assert messages[3].role == MessageRole.USER
        assert messages[3].content == "Follow-up question"

    def test_generate_cache_key(self, query_orchestrator):
        """Test cache key generation."""
        key1 = query_orchestrator._generate_cache_key("prompt1")
        key2 = query_orchestrator._generate_cache_key("prompt2")
        key3 = query_orchestrator._generate_cache_key("prompt1")

        # Different prompts should generate different keys
        assert key1 != key2

        # Same prompts should generate same keys
        assert key1 == key3

    def test_generate_cache_key_with_options(self, query_orchestrator):
        """Test cache key generation with different options."""
        key1 = query_orchestrator._generate_cache_key(
            "prompt", options={"model": "model1"}
        )
        key2 = query_orchestrator._generate_cache_key(
            "prompt", options={"model": "model2"}
        )

        # Different options should generate different keys
        assert key1 != key2

    @pytest.mark.asyncio
    async def test_error_handling_in_orchestrate_query(
        self, query_orchestrator, mock_service, mock_cache_service
    ):
        """Test error handling in query orchestration."""
        mock_cache_service.get.return_value = None
        mock_service._call_provider_api.side_effect = Exception("API error")

        with pytest.raises(LLMServiceException) as exc_info:
            await query_orchestrator.orchestrate_query(
                service=mock_service,
                prompt="Test prompt",
            )

        assert "Query orchestration failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_error_handling_in_streaming_query(
        self, query_orchestrator, mock_service
    ):
        """Test error handling in streaming query orchestration."""

        # Mock stream method to raise an exception
        async def error_stream(options):
            raise Exception("Streaming error")

        mock_service._stream_provider_api = error_stream

        with pytest.raises(LLMServiceException) as exc_info:
            async for _ in query_orchestrator.orchestrate_streaming_query(
                service=mock_service,
                prompt="Test prompt",
            ):
                pass

        assert "Streaming query orchestration failed" in str(exc_info.value)
