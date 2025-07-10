"""
Unit tests for LLM service base class.

This module contains tests for the abstract base class LLMServiceBase.
Since it's an abstract class, we test it through a minimal concrete implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, Optional, List, AsyncGenerator

from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    ProviderCapabilities,
    MessageItem,
    MessageRole,
    FunctionDefinition,
    ToolChoice,
    LLMUsage,
)


class ConcreteLLMService(LLMServiceBase):
    """Concrete implementation of LLMServiceBase for testing."""

    def __init__(self):
        self.capabilities = ProviderCapabilities(
            available_models=["test-model"],
            max_tokens={"test-model": 4000},
            supports_streaming=True,
            supports_function_calling=True,
        )

    async def get_capabilities(self) -> ProviderCapabilities:
        return self.capabilities

    async def estimate_tokens(self, text: str) -> int:
        return len(text) // 4  # Simple approximation

    async def _prepare_provider_options(
        self,
        prompt: str,
        conversation_history: Optional[List[MessageItem]] = None,
        options: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[FunctionDefinition]] = None,
        tool_choice: Optional[ToolChoice] = None,
    ) -> Dict[str, Any]:
        return {
            "messages": [{"role": "user", "content": prompt}],
            "model": options.get("model", "test-model") if options else "test-model",
        }

    async def _call_provider_api(self, options: Dict[str, Any]) -> Any:
        return {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

    async def _stream_provider_api(
        self, options: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        chunks = ["Test ", "streaming ", "response"]
        for chunk in chunks:
            yield chunk

    async def _convert_provider_response(
        self, raw_response: Any, options: Dict[str, Any]
    ) -> LLMResponse:
        return LLMResponse(
            content="Test response",
            provider="test",
            model=options.get("model", "test-model"),
            usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )


class TestLLMServiceBase:
    """Test the abstract base class through concrete implementation."""

    @pytest.fixture
    def service(self):
        return ConcreteLLMService()

    @pytest.mark.asyncio
    async def test_get_capabilities(self, service):
        """Test capabilities retrieval."""
        capabilities = await service.get_capabilities()

        assert isinstance(capabilities, ProviderCapabilities)
        assert "test-model" in capabilities.available_models
        assert capabilities.max_tokens["test-model"] == 4000
        assert capabilities.supports_streaming is True
        assert capabilities.supports_function_calling is True

    @pytest.mark.asyncio
    async def test_estimate_tokens(self, service):
        """Test token estimation."""
        text = "This is a test message"
        tokens = await service.estimate_tokens(text)

        assert isinstance(tokens, int)
        assert tokens > 0
        assert tokens == len(text) // 4  # Based on our implementation

    @pytest.mark.asyncio
    async def test_prepare_provider_options(self, service):
        """Test provider options preparation."""
        prompt = "Test prompt"
        options = {"model": "custom-model", "temperature": 0.7}

        prepared = await service._prepare_provider_options(prompt, options=options)

        assert isinstance(prepared, dict)
        assert "messages" in prepared
        assert prepared["model"] == "custom-model"
        assert prepared["messages"][0]["content"] == prompt

    @pytest.mark.asyncio
    async def test_call_provider_api(self, service):
        """Test provider API call."""
        options = {"model": "test-model"}

        response = await service._call_provider_api(options)

        assert isinstance(response, dict)
        assert "choices" in response
        assert "usage" in response

    @pytest.mark.asyncio
    async def test_stream_provider_api(self, service):
        """Test provider streaming API."""
        options = {"model": "test-model"}

        chunks = []
        async for chunk in service._stream_provider_api(options):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert "".join(chunks) == "Test streaming response"

    @pytest.mark.asyncio
    async def test_convert_provider_response(self, service):
        """Test provider response conversion."""
        raw_response = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }
        options = {"model": "test-model"}

        response = await service._convert_provider_response(raw_response, options)

        assert isinstance(response, LLMResponse)
        assert response.content == "Test response"
        assert response.provider == "test"
        assert response.model == "test-model"
        assert response.usage.total_tokens == 15

    def test_interface_methods_not_implemented(self, service):
        """Test that interface methods raise NotImplementedError."""
        # These methods should be implemented by concrete classes using LLMServiceCommon
        with pytest.raises(NotImplementedError):
            # Use asyncio.run to test async methods that should raise NotImplementedError
            import asyncio

            asyncio.run(service.query("test"))

        with pytest.raises(NotImplementedError):
            import asyncio

            async def test_stream():
                # stream_query should return an async generator that raises NotImplementedError
                try:
                    result = service.stream_query("test")
                    # If it returns a coroutine, await it to get the NotImplementedError
                    if hasattr(result, "__aiter__"):
                        async for chunk in result:
                            pass
                    else:
                        # If it's a coroutine, await it
                        await result
                except NotImplementedError:
                    raise  # Re-raise the expected error
                except TypeError as e:
                    # If we get a TypeError about __aiter__, that means the method
                    # is not properly implemented as an async generator
                    if "'async for' requires an object with __aiter__ method" in str(e):
                        raise NotImplementedError(
                            "stream_query should be an async generator"
                        )
                    else:
                        raise

            asyncio.run(test_stream())

        with pytest.raises(NotImplementedError):
            import asyncio

            asyncio.run(service.format_prompt("template", {}))


class TestAbstractMethods:
    """Test that abstract methods are properly enforced."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that the abstract class cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMServiceBase()

    def test_missing_abstract_method_implementation(self):
        """Test that classes missing abstract methods cannot be instantiated."""

        class IncompleteService(LLMServiceBase):
            # Missing all abstract methods
            pass

        with pytest.raises(TypeError):
            IncompleteService()

    def test_partial_abstract_method_implementation(self):
        """Test that classes with partial implementation cannot be instantiated."""

        class PartialService(LLMServiceBase):
            async def get_capabilities(self):
                pass

            # Missing other abstract methods

        with pytest.raises(TypeError):
            PartialService()


class TestLLMServiceBaseIntegration:
    """Integration tests for the base class design."""

    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test a complete workflow through the abstract interface."""
        service = ConcreteLLMService()

        # Test capabilities
        capabilities = await service.get_capabilities()
        assert "test-model" in capabilities.available_models

        # Test token estimation
        tokens = await service.estimate_tokens("Hello world")
        assert tokens > 0

        # Test API workflow
        options = await service._prepare_provider_options("Test prompt")
        raw_response = await service._call_provider_api(options)
        response = await service._convert_provider_response(raw_response, options)

        assert response.content == "Test response"
        assert response.provider == "test"

    @pytest.mark.asyncio
    async def test_streaming_workflow(self):
        """Test streaming workflow through the abstract interface."""
        service = ConcreteLLMService()

        options = await service._prepare_provider_options("Test prompt")

        full_response = ""
        async for chunk in service._stream_provider_api(options):
            full_response += chunk

        assert full_response == "Test streaming response"
