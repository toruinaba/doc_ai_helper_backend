"""
Unit tests for new parameter grouping and request models.

This module tests the new structured request format and its conversion
to/from legacy format.
"""

import pytest
from pydantic import ValidationError

from doc_ai_helper_backend.models.llm import (
    LLMQueryRequest,
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


class TestLLMQueryRequest:
    """Test LLMQueryRequest model."""
    
    def test_minimal_v2_request(self):
        """Test minimal v2 request."""
        core_query = CoreQueryRequest(prompt="Test prompt")
        request = LLMQueryRequest(query=core_query)
        
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
        
        request = LLMQueryRequest(
            query=core_query,
            tools=tools,
            document=document,
            processing=processing
        )
        
        assert request.query.prompt == "Test prompt"
        assert request.tools.enable_tools is True
        assert request.document.context_documents == ["README.md"]
        assert request.processing.disable_cache is True

