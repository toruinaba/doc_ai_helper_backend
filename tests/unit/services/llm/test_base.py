"""
Test suite for LLMServiceBase

Tests the abstract base class for LLM services, including interface methods
and abstract method definitions.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, Optional, List, AsyncGenerator

from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    ProviderCapabilities,
    MessageItem,
    MessageRole,
    FunctionCall,
    FunctionDefinition,
    ToolCall,
    ToolChoice,
    LLMUsage,
)


class ConcreteLLMService(LLMServiceBase):
    """Concrete implementation for testing abstract base class."""
    
    def __init__(self):
        self.capabilities = ProviderCapabilities(
            available_models=["test-model-1", "test-model-2"],
            max_tokens={"test-model-1": 4000, "test-model-2": 8000},
            supports_streaming=True,
            supports_function_calling=True
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
            "prompt": prompt,
            "conversation_history": conversation_history,
            "options": options or {},
            "system_prompt": system_prompt,
            "tools": tools,
            "tool_choice": tool_choice,
        }
        
    async def _call_provider_api(self, options: Dict[str, Any]) -> Any:
        return {
            "content": f"Response to: {options['prompt']}",
            "model": "test-model",
            "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
        }
        
    async def _stream_provider_api(
        self, options: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        chunks = ["Hello", " ", "world", "!"]
        for chunk in chunks:
            yield chunk
            
    async def _convert_provider_response(
        self, raw_response: Any, options: Dict[str, Any]
    ) -> LLMResponse:
        return LLMResponse(
            content=raw_response["content"],
            model=raw_response["model"],
            provider="test",
            usage=LLMUsage(**raw_response["usage"])
        )


class TestLLMServiceBase:
    """Test LLMServiceBase abstract class."""
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that abstract class cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMServiceBase()

    def test_concrete_implementation_works(self):
        """Test that concrete implementation can be instantiated."""
        service = ConcreteLLMService()
        assert isinstance(service, LLMServiceBase)
        assert isinstance(service, ConcreteLLMService)

    async def test_get_capabilities(self):
        """Test get_capabilities abstract method implementation."""
        service = ConcreteLLMService()
        capabilities = await service.get_capabilities()
        
        assert isinstance(capabilities, ProviderCapabilities)
        assert capabilities.available_models == ["test-model-1", "test-model-2"]
        assert capabilities.supports_streaming is True
        assert capabilities.supports_function_calling is True
        assert capabilities.max_tokens == {"test-model-1": 4000, "test-model-2": 8000}

    async def test_estimate_tokens(self):
        """Test estimate_tokens abstract method implementation."""
        service = ConcreteLLMService()
        
        tokens = await service.estimate_tokens("Hello world")
        assert isinstance(tokens, int)
        assert tokens > 0
        
        # Test with longer text
        long_text = "This is a longer text" * 10
        long_tokens = await service.estimate_tokens(long_text)
        assert long_tokens > tokens

    async def test_prepare_provider_options_basic(self):
        """Test _prepare_provider_options with basic parameters."""
        service = ConcreteLLMService()
        
        options = await service._prepare_provider_options(
            prompt="Test prompt"
        )
        
        assert options["prompt"] == "Test prompt"
        assert options["conversation_history"] is None
        assert options["options"] == {}
        assert options["system_prompt"] is None
        assert options["tools"] is None
        assert options["tool_choice"] is None

    async def test_prepare_provider_options_full(self):
        """Test _prepare_provider_options with all parameters."""
        service = ConcreteLLMService()
        
        history = [MessageItem(role=MessageRole.USER, content="Previous message")]
        options_dict = {"temperature": 0.7}
        system_prompt = "You are a helpful assistant"
        tools = [FunctionDefinition(
            name="test_function",
            description="A test function",
            parameters={"type": "object", "properties": {}}
        )]
        tool_choice = ToolChoice(type="auto")
        
        options = await service._prepare_provider_options(
            prompt="Test prompt",
            conversation_history=history,
            options=options_dict,
            system_prompt=system_prompt,
            tools=tools,
            tool_choice=tool_choice,
        )
        
        assert options["prompt"] == "Test prompt"
        assert options["conversation_history"] == history
        assert options["options"] == options_dict
        assert options["system_prompt"] == system_prompt
        assert options["tools"] == tools
        assert options["tool_choice"] == tool_choice

    async def test_call_provider_api(self):
        """Test _call_provider_api abstract method implementation."""
        service = ConcreteLLMService()
        
        options = {"prompt": "Test prompt"}
        response = await service._call_provider_api(options)
        
        assert response["content"] == "Response to: Test prompt"
        assert response["model"] == "test-model"
        assert "usage" in response

    async def test_stream_provider_api(self):
        """Test _stream_provider_api abstract method implementation."""
        service = ConcreteLLMService()
        
        options = {"prompt": "Test prompt"}
        chunks = []
        
        async for chunk in service._stream_provider_api(options):
            chunks.append(chunk)
            
        assert chunks == ["Hello", " ", "world", "!"]

    async def test_convert_provider_response(self):
        """Test _convert_provider_response abstract method implementation."""
        service = ConcreteLLMService()
        
        raw_response = {
            "content": "Test response",
            "model": "test-model",
            "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
        }
        options = {"prompt": "Test prompt"}
        
        llm_response = await service._convert_provider_response(raw_response, options)
        
        assert isinstance(llm_response, LLMResponse)
        assert llm_response.content == "Test response"
        assert llm_response.model == "test-model"
        assert llm_response.provider == "test"
        assert llm_response.usage.prompt_tokens == 10
        assert llm_response.usage.completion_tokens == 15
        assert llm_response.usage.total_tokens == 25


class TestLLMServiceBaseInterfaceMethods:
    """Test interface methods that should raise NotImplementedError."""
    
    def setup_method(self):
        self.service = ConcreteLLMService()

    async def test_query_not_implemented(self):
        """Test query method raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="Concrete classes must implement query method"):
            await self.service.query("Test prompt")

    async def test_stream_query_not_implemented(self):
        """Test stream_query method raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="Concrete classes must implement stream_query method"):
            # stream_query raises NotImplementedError, so we need to handle the coroutine properly
            stream = self.service.stream_query("Test prompt")
            try:
                async for chunk in stream:
                    pass
            except TypeError:
                # If it returns a coroutine instead of async generator, await it to get the exception
                await stream

    async def test_query_with_tools_not_implemented(self):
        """Test query_with_tools method raises NotImplementedError."""
        tools = [FunctionDefinition(
            name="test_function",
            description="A test function",
            parameters={"type": "object", "properties": {}}
        )]
        
        with pytest.raises(NotImplementedError, match="Concrete classes must implement query_with_tools method"):
            await self.service.query_with_tools("Test prompt", tools)

    async def test_query_with_tools_and_followup_not_implemented(self):
        """Test query_with_tools_and_followup method raises NotImplementedError."""
        tools = [FunctionDefinition(
            name="test_function",
            description="A test function",
            parameters={"type": "object", "properties": {}}
        )]
        
        with pytest.raises(NotImplementedError, match="Concrete classes must implement query_with_tools_and_followup method"):
            await self.service.query_with_tools_and_followup("Test prompt", tools)

    async def test_execute_function_call_not_implemented(self):
        """Test execute_function_call method raises NotImplementedError."""
        function_call = FunctionCall(name="test_function", arguments='{}')
        available_functions = {}
        
        with pytest.raises(NotImplementedError, match="Concrete classes must implement execute_function_call method"):
            await self.service.execute_function_call(function_call, available_functions)

    async def test_get_available_functions_not_implemented(self):
        """Test get_available_functions method raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="Concrete classes must implement get_available_functions method"):
            await self.service.get_available_functions()

    async def test_format_prompt_not_implemented(self):
        """Test format_prompt method raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="Concrete classes must implement format_prompt method"):
            await self.service.format_prompt("test_template", {})

    async def test_get_available_templates_not_implemented(self):
        """Test get_available_templates method raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="Concrete classes must implement get_available_templates method"):
            await self.service.get_available_templates()


class IncompleteService(LLMServiceBase):
    """Incomplete service implementation to test abstract method enforcement."""
    
    async def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            available_models=["incomplete-model"],
            max_tokens={"incomplete-model": 1000},
            supports_streaming=False,
            supports_function_calling=False
        )
    
    # Missing other abstract methods


class TestAbstractMethodEnforcement:
    """Test that abstract methods must be implemented."""
    
    def test_incomplete_service_cannot_be_instantiated(self):
        """Test that incomplete service implementation cannot be instantiated."""
        with pytest.raises(TypeError):
            IncompleteService()


class TestProviderCapabilities:
    """Test ProviderCapabilities model used by the base class."""
    
    def test_provider_capabilities_creation(self):
        """Test creating ProviderCapabilities object."""
        capabilities = ProviderCapabilities(
            available_models=["test-model"],
            max_tokens={"test-model": 2000},
            supports_streaming=True,
            supports_function_calling=False
        )
        
        assert capabilities.available_models == ["test-model"]
        assert capabilities.supports_streaming is True
        assert capabilities.supports_function_calling is False
        assert capabilities.max_tokens == {"test-model": 2000}

    def test_provider_capabilities_defaults(self):
        """Test ProviderCapabilities with minimal parameters."""
        capabilities = ProviderCapabilities(
            available_models=["minimal-model"],
            max_tokens={"minimal-model": 1000}
        )
        
        assert capabilities.available_models == ["minimal-model"]
        assert capabilities.max_tokens == {"minimal-model": 1000}
        # Other fields should have their default values
        assert capabilities.supports_streaming is not None
        assert capabilities.supports_function_calling is not None