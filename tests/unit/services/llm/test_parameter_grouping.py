"""
Unit tests for new parameter grouping and request models.

This module tests the new structured request format and its conversion
to/from legacy format.
"""

import pytest
from pydantic import ValidationError

from doc_ai_helper_backend.models.llm import (
    LLMQueryRequest,
    LLMQueryRequestV2,
    CoreQueryRequest,
    ToolConfiguration,
    DocumentContext,
    ProcessingOptions,
    MessageItem,
)


class TestCoreQueryRequest:
    """Test CoreQueryRequest model."""
    
    def test_valid_core_request(self):
        """Test valid core query request."""
        request = CoreQueryRequest(
            prompt="Test prompt",
            provider="openai",
            model="gpt-3.5-turbo"
        )
        
        assert request.prompt == "Test prompt"
        assert request.provider == "openai"
        assert request.model == "gpt-3.5-turbo"
        assert request.conversation_history is None
    
    def test_prompt_validation(self):
        """Test prompt validation."""
        # Empty prompt should fail
        with pytest.raises(ValidationError):
            CoreQueryRequest(prompt="")
        
        # Whitespace-only prompt should fail
        with pytest.raises(ValidationError):
            CoreQueryRequest(prompt="   ")
        
        # Valid prompt should pass
        request = CoreQueryRequest(prompt="Valid prompt")
        assert request.prompt == "Valid prompt"
    
    def test_default_provider(self):
        """Test default provider setting."""
        request = CoreQueryRequest(prompt="Test")
        assert request.provider == "openai"


class TestToolConfiguration:
    """Test ToolConfiguration model."""
    
    def test_default_tool_config(self):
        """Test default tool configuration."""
        config = ToolConfiguration()
        
        assert config.enable_tools is False
        assert config.tool_choice == "auto"
        assert config.complete_tool_flow is True
    
    def test_tool_config_with_values(self):
        """Test tool configuration with custom values."""
        config = ToolConfiguration(
            enable_tools=True,
            tool_choice="required",
            complete_tool_flow=False
        )
        
        assert config.enable_tools is True
        assert config.tool_choice == "required"
        assert config.complete_tool_flow is False


class TestDocumentContext:
    """Test DocumentContext model."""
    
    def test_default_document_context(self):
        """Test default document context."""
        context = DocumentContext()
        
        assert context.repository_context is None
        assert context.document_metadata is None
        assert context.auto_include_document is True
        assert context.context_documents is None
    
    def test_document_context_with_values(self):
        """Test document context with custom values."""
        context = DocumentContext(
            auto_include_document=False,
            context_documents=["doc1.md", "doc2.md"]
        )
        
        assert context.auto_include_document is False
        assert context.context_documents == ["doc1.md", "doc2.md"]


class TestProcessingOptions:
    """Test ProcessingOptions model."""
    
    def test_default_processing_options(self):
        """Test default processing options."""
        options = ProcessingOptions()
        
        assert options.disable_cache is False
        assert options.options == {}
    
    def test_processing_options_with_values(self):
        """Test processing options with custom values."""
        options = ProcessingOptions(
            disable_cache=True,
            options={"temperature": 0.7, "max_tokens": 100}
        )
        
        assert options.disable_cache is True
        assert options.options["temperature"] == 0.7
        assert options.options["max_tokens"] == 100


class TestLLMQueryRequestV2:
    """Test LLMQueryRequestV2 model."""
    
    def test_minimal_v2_request(self):
        """Test minimal v2 request."""
        core_query = CoreQueryRequest(prompt="Test prompt")
        request = LLMQueryRequestV2(query=core_query)
        
        assert request.query.prompt == "Test prompt"
        assert request.tools is None
        assert request.document is None
        assert request.processing is None
    
    def test_full_v2_request(self):
        """Test v2 request with all components."""
        core_query = CoreQueryRequest(
            prompt="Test prompt",
            provider="openai",
            model="gpt-4"
        )
        
        tools = ToolConfiguration(
            enable_tools=True,
            tool_choice="auto"
        )
        
        document = DocumentContext(
            auto_include_document=True,
            context_documents=["README.md"]
        )
        
        processing = ProcessingOptions(
            disable_cache=True,
            options={"temperature": 0.5}
        )
        
        request = LLMQueryRequestV2(
            query=core_query,
            tools=tools,
            document=document,
            processing=processing
        )
        
        assert request.query.prompt == "Test prompt"
        assert request.tools.enable_tools is True
        assert request.document.context_documents == ["README.md"]
        assert request.processing.disable_cache is True


class TestLegacyConversion:
    """Test conversion between legacy and v2 formats."""
    
    def test_simple_legacy_to_v2_conversion(self):
        """Test simple legacy to v2 conversion."""
        legacy = LLMQueryRequest(
            prompt="Test prompt",
            provider="openai",
            model="gpt-3.5-turbo"
        )
        
        v2 = LLMQueryRequestV2.from_legacy_request(legacy)
        
        assert v2.query.prompt == "Test prompt"
        assert v2.query.provider == "openai"
        assert v2.query.model == "gpt-3.5-turbo"
        assert v2.tools is None
        assert v2.document is None
        assert v2.processing is None
    
    def test_complex_legacy_to_v2_conversion(self):
        """Test complex legacy to v2 conversion."""
        legacy = LLMQueryRequest(
            prompt="Test prompt",
            provider="openai",
            enable_tools=True,
            tool_choice="required",
            context_documents=["doc1.md"],
            disable_cache=True,
            options={"temperature": 0.7}
        )
        
        v2 = LLMQueryRequestV2.from_legacy_request(legacy)
        
        # Check core query
        assert v2.query.prompt == "Test prompt"
        assert v2.query.provider == "openai"
        
        # Check tools
        assert v2.tools is not None
        assert v2.tools.enable_tools is True
        assert v2.tools.tool_choice == "required"
        
        # Check document
        assert v2.document is not None
        assert v2.document.context_documents == ["doc1.md"]
        
        # Check processing
        assert v2.processing is not None
        assert v2.processing.disable_cache is True
        assert v2.processing.options["temperature"] == 0.7
    
    def test_v2_to_legacy_conversion(self):
        """Test v2 to legacy conversion."""
        core_query = CoreQueryRequest(
            prompt="Test prompt",
            provider="openai"
        )
        
        tools = ToolConfiguration(
            enable_tools=True,
            tool_choice="auto"
        )
        
        v2 = LLMQueryRequestV2(
            query=core_query,
            tools=tools
        )
        
        legacy = v2.to_legacy_request()
        
        assert legacy.prompt == "Test prompt"
        assert legacy.provider == "openai"
        assert legacy.enable_tools is True
        assert legacy.tool_choice == "auto"
    
    def test_round_trip_conversion(self):
        """Test round-trip conversion (legacy -> v2 -> legacy)."""
        original_legacy = LLMQueryRequest(
            prompt="Test prompt",
            provider="openai",
            enable_tools=True,
            tool_choice="required",
            complete_tool_flow=False,
            context_documents=["doc1.md", "doc2.md"],
            disable_cache=True,
            options={"temperature": 0.8, "max_tokens": 200}
        )
        
        # Convert to v2
        v2 = LLMQueryRequestV2.from_legacy_request(original_legacy)
        
        # Convert back to legacy
        converted_legacy = v2.to_legacy_request()
        
        # Compare key fields
        assert converted_legacy.prompt == original_legacy.prompt
        assert converted_legacy.provider == original_legacy.provider
        assert converted_legacy.enable_tools == original_legacy.enable_tools
        assert converted_legacy.tool_choice == original_legacy.tool_choice
        assert converted_legacy.complete_tool_flow == original_legacy.complete_tool_flow
        assert converted_legacy.context_documents == original_legacy.context_documents
        assert converted_legacy.disable_cache == original_legacy.disable_cache
        assert converted_legacy.options == original_legacy.options
    
    def test_legacy_with_conversation_history(self):
        """Test legacy conversion with conversation history."""
        messages = [
            MessageItem(role="user", content="Hello"),
            MessageItem(role="assistant", content="Hi there!")
        ]
        
        legacy = LLMQueryRequest(
            prompt="Continue the conversation",
            conversation_history=messages
        )
        
        v2 = LLMQueryRequestV2.from_legacy_request(legacy)
        
        assert v2.query.conversation_history is not None
        assert len(v2.query.conversation_history) == 2
        assert v2.query.conversation_history[0].role == "user"
        assert v2.query.conversation_history[0].content == "Hello"
        assert v2.query.conversation_history[1].role == "assistant"
        assert v2.query.conversation_history[1].content == "Hi there!"
    
    def test_legacy_with_only_tools_enabled(self):
        """Test legacy conversion with only tools enabled."""
        legacy = LLMQueryRequest(
            prompt="Test prompt",
            enable_tools=True
            # Other tool fields use defaults
        )
        
        v2 = LLMQueryRequestV2.from_legacy_request(legacy)
        
        assert v2.tools is not None
        assert v2.tools.enable_tools is True
        assert v2.tools.tool_choice == "auto"  # Default value
        assert v2.tools.complete_tool_flow is True  # Default value
    
    def test_legacy_with_minimal_document_context(self):
        """Test legacy conversion with minimal document context."""
        legacy = LLMQueryRequest(
            prompt="Test prompt",
            auto_include_document=False  # Non-default value
        )
        
        v2 = LLMQueryRequestV2.from_legacy_request(legacy)
        
        # Should create document context because auto_include_document is non-default
        assert v2.document is not None
        assert v2.document.auto_include_document is False