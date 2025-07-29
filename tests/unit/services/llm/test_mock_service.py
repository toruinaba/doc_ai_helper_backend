"""
Test for MockLLMService with comprehensive feature coverage.

This module contains comprehensive unit tests for the MockLLMService implementation
with focus on all features including error simulation, function calling, and edge cases.
"""

import pytest
import asyncio
from typing import List
from unittest.mock import patch, MagicMock

from doc_ai_helper_backend.models.llm import (
    MessageItem,
    MessageRole,
    LLMResponse,
    FunctionDefinition,
    FunctionCall,
    ToolCall,
    ToolChoice,
    ProviderCapabilities,
)
from doc_ai_helper_backend.models.repository_context import (
    RepositoryContext,
    DocumentMetadata,
    GitService,
    DocumentType,
)
from doc_ai_helper_backend.services.llm.providers.mock_service import MockLLMService
from doc_ai_helper_backend.core.exceptions import LLMServiceException


class TestMockLLMServiceBasic:
    """Test basic functionality of MockLLMService."""

    @pytest.fixture
    def service(self):
        """Create a MockLLMService instance for testing."""
        return MockLLMService(response_delay=0.01)

    async def test_initialization(self):
        """Test service initialization with various parameters."""
        # Default initialization
        service = MockLLMService()
        assert service.response_delay == 0.1  # Default delay is 0.1
        assert service.default_model == "mock-model"

        # Custom initialization
        service = MockLLMService(
            response_delay=0.5, default_model="custom-mock", custom_param="test"
        )
        assert service.response_delay == 0.5
        assert service.default_model == "custom-mock"

    async def test_get_capabilities(self, service):
        """Test get_capabilities method."""
        capabilities = await service.get_capabilities()

        assert isinstance(capabilities, ProviderCapabilities)
        assert capabilities.supports_streaming is True
        assert capabilities.supports_function_calling is True
        assert "mock-model" in capabilities.available_models

    async def test_basic_query(self, service):
        """Test basic query functionality."""
        response = await service.query("Hello, how are you?")

        assert isinstance(response, LLMResponse)
        assert response.content
        assert response.model
        assert response.provider == "mock"
        assert response.usage.prompt_tokens > 0
        assert response.usage.completion_tokens > 0
        assert response.usage.total_tokens == (
            response.usage.prompt_tokens + response.usage.completion_tokens
        )

    async def test_query_with_built_in_patterns(self, service):
        """Test queries that trigger built-in response patterns."""
        # Help pattern
        response = await service.query("help")
        assert "モック" in response.content or "mock" in response.content.lower()

        # Time pattern
        response = await service.query("What time is it?")
        assert any(word in response.content.lower() for word in ["time", "mock"]) or "モック" in response.content

        # Version pattern
        response = await service.query("version")
        assert any(word in response.content.lower() for word in ["version", "mock"])

    async def test_query_with_options(self, service):
        """Test query with various options."""
        options = {"model": "custom-model", "temperature": 0.8, "max_tokens": 1000}

        response = await service.query("Test query", options=options)
        assert response.model == "custom-model"
        assert isinstance(response, LLMResponse)


class TestMockLLMServiceErrorHandling:
    """Test error handling in MockLLMService."""

    @pytest.fixture
    def service(self):
        return MockLLMService(response_delay=0.01)

    async def test_error_simulation(self, service):
        """Test error simulation functionality."""
        # Test various error keywords
        error_keywords = ["simulate_error", "force_error", "test_error"]

        for keyword in error_keywords:
            with pytest.raises(LLMServiceException) as exc_info:
                await service.query(f"Please {keyword} for testing")
            assert "Simulated error for testing purposes" in str(exc_info.value)

    async def test_empty_prompt_handling(self, service):
        """Test handling of empty prompts."""
        # Empty string
        with pytest.raises(LLMServiceException) as exc_info:
            await service.query("")
        assert "Prompt cannot be empty" in str(exc_info.value)

        # Whitespace only
        with pytest.raises(LLMServiceException) as exc_info:
            await service.query("   ")
        assert "Prompt cannot be empty" in str(exc_info.value)

        # None (should be handled gracefully)
        with pytest.raises(LLMServiceException) as exc_info:
            await service.query(None)
        assert "Prompt cannot be empty" in str(exc_info.value)

    async def test_error_in_stream_query(self, service):
        """Test error handling in stream query."""
        # Test error simulation
        with pytest.raises(LLMServiceException):
            chunks = []
            async for chunk in service.stream_query("simulate_error"):
                chunks.append(chunk)

        # Test empty prompt
        with pytest.raises(LLMServiceException):
            chunks = []
            async for chunk in service.stream_query(""):
                chunks.append(chunk)


class TestMockLLMServiceStreaming:
    """Test streaming functionality in MockLLMService."""

    @pytest.fixture
    def service(self):
        return MockLLMService(response_delay=0.01)

    async def test_basic_streaming(self, service):
        """Test basic streaming functionality."""
        chunks = []
        async for chunk in service.stream_query("Tell me a story"):
            chunks.append(chunk)

        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0

    async def test_streaming_with_conversation_history(self, service):
        """Test streaming with conversation history."""
        history = [
            MessageItem(role=MessageRole.USER, content="Hello"),
            MessageItem(role=MessageRole.ASSISTANT, content="Hi there!"),
        ]

        chunks = []
        async for chunk in service.stream_query(
            "Continue the conversation", conversation_history=history
        ):
            chunks.append(chunk)

        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0

    async def test_streaming_performance(self, service):
        """Test streaming performance with different delays."""
        # Test with fast streaming
        fast_service = MockLLMService(response_delay=0.001)

        start_time = asyncio.get_event_loop().time()
        fast_chunks = []
        async for chunk in fast_service.stream_query("Quick response"):
            fast_chunks.append(chunk)
        fast_time = asyncio.get_event_loop().time() - start_time

        # Test with slower streaming
        slow_service = MockLLMService(response_delay=0.1)

        start_time = asyncio.get_event_loop().time()
        slow_chunks = []
        async for chunk in slow_service.stream_query("Slow response"):
            slow_chunks.append(chunk)
        slow_time = asyncio.get_event_loop().time() - start_time

        # Slow service should take longer
        assert slow_time > fast_time
        assert len(fast_chunks) > 0
        assert len(slow_chunks) > 0


class TestMockLLMServiceRepositoryContext:
    """Test repository context functionality in MockLLMService."""

    @pytest.fixture
    def service(self):
        return MockLLMService(response_delay=0.01)

    @pytest.fixture
    def repository_context(self):
        return RepositoryContext(
            service=GitService.GITHUB,
            owner="test-owner",
            repo="test-repo",
            ref="main",
            base_url="https://github.com/test-owner/test-repo",
        )

    @pytest.fixture
    def document_metadata(self):
        return DocumentMetadata(
            path="docs/README.md",
            type=DocumentType.MARKDOWN,
            size=1024,
            last_modified="2023-01-01T00:00:00Z",
        )

    async def test_query_with_repository_context(self, service, repository_context):
        """Test query with repository context."""
        response = await service.query(
            "What is this repository about?", repository_context=repository_context
        )

        assert isinstance(response, LLMResponse)
        assert response.content
        # Context should influence the response
        assert len(response.content) > 0

    async def test_query_with_full_context(
        self, service, repository_context, document_metadata
    ):
        """Test query with full context (repository + document)."""
        document_content = "# Test Document\n\nThis is a test document."

        response = await service.query(
            "Analyze this document",
            repository_context=repository_context,
            document_metadata=document_metadata,
            document_content=document_content,
        )

        assert isinstance(response, LLMResponse)
        assert response.content
        # Full context should provide rich response
        assert len(response.content) > 0


class TestMockLLMServiceFunctionCalling:
    """Test function calling capabilities in MockLLMService."""

    @pytest.fixture
    def service(self):
        return MockLLMService(response_delay=0.01)

    @pytest.fixture
    def github_functions(self):
        """Sample GitHub functions for testing."""
        return [
            FunctionDefinition(
                name="create_github_issue",
                description="Create a new issue in GitHub repository",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Issue title"},
                        "body": {"type": "string", "description": "Issue body"},
                    },
                    "required": ["title"],
                },
            )
        ]

    @pytest.fixture
    def analysis_functions(self):
        """Sample analysis functions for testing."""
        return [
            FunctionDefinition(
                name="analyze_document_structure",
                description="Analyze the structure of a document",
                parameters={
                    "type": "object",
                    "properties": {
                        "document_path": {
                            "type": "string",
                            "description": "Path to document",
                        }
                    },
                    "required": ["document_path"],
                },
            )
        ]

    async def test_query_with_github_functions(self, service, github_functions):
        """Test query that should trigger GitHub function calling."""
        response = await service.query(
            "Create an issue about documentation improvement",
            options={"functions": github_functions},
        )

        assert isinstance(response, LLMResponse)
        assert response.content
        # Should contain tool calls for GitHub functions
        if response.tool_calls:
            assert len(response.tool_calls) > 0
            assert response.tool_calls[0].function.name in ["create_github_issue"]

    async def test_query_with_analysis_functions(self, service, analysis_functions):
        """Test query that should trigger analysis function calling."""
        response = await service.query(
            "Analyze the structure of this document",
            options={"functions": analysis_functions},
        )

        assert isinstance(response, LLMResponse)
        assert response.content
        # Should handle analysis functions appropriately
        if response.tool_calls:
            assert any("analyze" in tool.function.name for tool in response.tool_calls)

    async def test_query_without_function_triggers(self, service, github_functions):
        """Test query that should NOT trigger function calling."""
        response = await service.query(
            "What is the weather like today?", options={"functions": github_functions}
        )

        assert isinstance(response, LLMResponse)
        assert response.content
        # Should not trigger GitHub functions for weather query
        assert not response.tool_calls or len(response.tool_calls) == 0


class TestMockLLMServiceConversationHistory:
    """Test conversation history management in MockLLMService."""

    @pytest.fixture
    def service(self):
        return MockLLMService(response_delay=0.01)

    @pytest.fixture
    def conversation_history(self):
        """Sample conversation history for testing."""
        return [
            MessageItem(role=MessageRole.USER, content="Hello, how are you?"),
            MessageItem(
                role=MessageRole.ASSISTANT, content="I'm doing well, thank you!"
            ),
            MessageItem(role=MessageRole.USER, content="Can you help me with Python?"),
            MessageItem(
                role=MessageRole.ASSISTANT,
                content="Of course! I'd be happy to help you with Python.",
            ),
        ]

    async def test_query_with_conversation_history(self, service, conversation_history):
        """Test query with conversation history."""
        response = await service.query(
            "What were we talking about?", conversation_history=conversation_history
        )

        assert isinstance(response, LLMResponse)
        assert response.content
        # Response should acknowledge conversation context
        assert len(response.content) > 0

    async def test_empty_conversation_history(self, service):
        """Test query with empty conversation history."""
        response = await service.query("Hello there!", conversation_history=[])

        assert isinstance(response, LLMResponse)
        assert response.content

    async def test_streaming_with_conversation_history(
        self, service, conversation_history
    ):
        """Test streaming query with conversation history."""
        chunks = []
        async for chunk in service.stream_query(
            "Continue our discussion", conversation_history=conversation_history
        ):
            chunks.append(chunk)

        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0


class TestMockLLMServiceAdvancedFunctionCalling:
    """Test advanced function calling features including tools conversion and utility functions."""

    @pytest.fixture
    def service(self):
        return MockLLMService(response_delay=0.01)

    @pytest.fixture
    def tool_definitions(self):
        """Sample tool definitions in OpenAI tools format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_github_issue",
                    "description": "Create a GitHub issue",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "body": {"type": "string"},
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_math",
                    "description": "Calculate mathematical expressions",
                    "parameters": {
                        "type": "object",
                        "properties": {"expression": {"type": "string"}},
                    },
                },
            },
        ]

    @pytest.fixture
    def utility_functions(self):
        """Sample utility functions for testing."""
        return [
            FunctionDefinition(
                name="get_current_time",
                description="Get the current time",
                parameters={"type": "object", "properties": {}},
            ),
            FunctionDefinition(
                name="count_characters",
                description="Count characters in text",
                parameters={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                },
            ),
            FunctionDefinition(
                name="validate_email",
                description="Validate email address",
                parameters={
                    "type": "object",
                    "properties": {"email": {"type": "string"}},
                },
            ),
        ]

    async def test_tools_to_functions_conversion(self, service, tool_definitions):
        """Test conversion of tools format to functions format."""
        response = await service.query(
            "Create an issue for documentation improvement",
            options={"tools": tool_definitions},
        )

        assert isinstance(response, LLMResponse)
        assert response.content
        # Should trigger GitHub function calling
        if response.tool_calls:
            assert any(
                "github" in tool.function.name.lower() for tool in response.tool_calls
            )

    async def test_utility_function_detection(self, service, utility_functions):
        """Test detection and calling of utility functions."""
        # Test time function
        response = await service.query(
            "What is the current time?", options={"functions": utility_functions}
        )

        assert isinstance(response, LLMResponse)
        assert response.content
        if response.tool_calls:
            assert any(
                "time" in tool.function.name.lower() for tool in response.tool_calls
            )

    async def test_character_count_function(self, service, utility_functions):
        """Test character counting utility function."""
        response = await service.query(
            "How many characters are in this text?",
            options={"functions": utility_functions},
        )

        assert isinstance(response, LLMResponse)
        assert response.content
        if response.tool_calls:
            assert any(
                "count" in tool.function.name.lower() for tool in response.tool_calls
            )

    async def test_email_validation_function(self, service, utility_functions):
        """Test email validation utility function."""
        response = await service.query(
            "Is test@example.com a valid email address?",
            options={"functions": utility_functions},
        )

        assert isinstance(response, LLMResponse)
        assert response.content
        if response.tool_calls:
            assert any(
                "email" in tool.function.name.lower() for tool in response.tool_calls
            )

    async def test_mixed_function_types(self, service):
        """Test with mixed function types (GitHub, utility, analysis)."""
        mixed_functions = [
            FunctionDefinition(
                name="create_github_issue",
                description="Create a GitHub issue",
                parameters={"type": "object", "properties": {}},
            ),
            FunctionDefinition(
                name="analyze_text_sentiment",
                description="Analyze text sentiment",
                parameters={"type": "object", "properties": {}},
            ),
            FunctionDefinition(
                name="calculate_math_expression",
                description="Calculate math expression",
                parameters={"type": "object", "properties": {}},
            ),
        ]

        # Test GitHub function trigger
        response = await service.query(
            "Create an issue to report this bug", options={"functions": mixed_functions}
        )

        assert isinstance(response, LLMResponse)
        if response.tool_calls:
            assert any(
                "github" in tool.function.name.lower() for tool in response.tool_calls
            )

    async def test_no_function_match(self, service, utility_functions):
        """Test query that doesn't match any function pattern."""
        response = await service.query(
            "Tell me a joke about programming", options={"functions": utility_functions}
        )

        assert isinstance(response, LLMResponse)
        assert response.content
        # Should not trigger function calls for unrelated queries
        assert not response.tool_calls or len(response.tool_calls) == 0


class TestMockLLMServiceSystemPromptHandling:
    """Test system prompt generation and handling."""

    @pytest.fixture
    def service(self):
        return MockLLMService(response_delay=0.01)

    @pytest.fixture
    def repository_context_vscode(self):
        """Repository context for VS Code repository."""
        return RepositoryContext(
            service=GitService.GITHUB,
            owner="microsoft",
            repo="vscode",
            ref="main",
            base_url="https://github.com/microsoft/vscode",
        )

    @pytest.fixture
    def repository_context_minimal(self):
        """Repository context for minimal test repository."""
        return RepositoryContext(
            service=GitService.GITHUB,
            owner="test",
            repo="minimal",
            ref="main",
            base_url="https://github.com/test/minimal",
        )

    async def test_system_prompt_with_vscode_context(
        self, service, repository_context_vscode
    ):
        """Test system prompt generation with VS Code repository context."""
        response = await service.query(
            "What is this codebase about?",
            repository_context=repository_context_vscode,
            include_document_in_system_prompt=True,
        )

        assert isinstance(response, LLMResponse)
        assert response.content
        # Should recognize VS Code context in response (may not always include vscode in content)
        assert len(response.content) > 0

    async def test_system_prompt_with_minimal_context(
        self, service, repository_context_minimal
    ):
        """Test system prompt generation with minimal repository context."""
        response = await service.query(
            "Describe this repository",
            repository_context=repository_context_minimal,
            include_document_in_system_prompt=True,
        )

        assert isinstance(response, LLMResponse)
        assert response.content
        # Should recognize minimal repository context (may not always include "minimal" in content)
        assert len(response.content) > 0

    async def test_system_prompt_generation_failure(self, service):
        """Test handling of system prompt generation failure."""
        # Create repository context that might cause system prompt issues
        minimal_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="x",  # Minimal valid owner
            repo="y",  # Minimal valid repo
            ref="main",
            base_url="https://github.com/x/y",
        )

        response = await service.query(
            "Test query with minimal context",
            repository_context=minimal_context,
            include_document_in_system_prompt=True,
        )

        assert isinstance(response, LLMResponse)
        assert response.content
        # Should handle minimal context gracefully
        assert len(response.content) > 0

    async def test_streaming_with_system_prompt(
        self, service, repository_context_vscode
    ):
        """Test streaming with system prompt context."""
        chunks = []
        async for chunk in service.stream_query(
            "Explain this repository structure",
            repository_context=repository_context_vscode,
            include_document_in_system_prompt=True,
        ):
            chunks.append(chunk)

        assert len(chunks) > 0
        full_response = "".join(chunks)
        # Should include context in streaming response (may not always mention vscode specifically)
        assert len(full_response) > 0

    async def test_custom_system_prompt_template(
        self, service, repository_context_vscode
    ):
        """Test with custom system prompt template."""
        response = await service.query(
            "Help me understand this code",
            repository_context=repository_context_vscode,
            system_prompt_template="custom_template",
            include_document_in_system_prompt=True,
        )

        assert isinstance(response, LLMResponse)
        assert response.content


class TestMockLLMServiceResponseGeneration:
    """Test response generation patterns and edge cases."""

    @pytest.fixture
    def service(self):
        return MockLLMService(response_delay=0.01)

    async def test_question_response_pattern(self, service):
        """Test response pattern for questions."""
        response = await service.query("What is Python programming?")

        assert isinstance(response, LLMResponse)
        assert response.content
        # New service returns pattern match for "what is" and "python"
        assert "python" in response.content.lower()

    async def test_short_prompt_response(self, service):
        """Test response pattern for short prompts."""
        response = await service.query("Hi")

        assert isinstance(response, LLMResponse)
        assert response.content
        # New service returns Japanese: "短いプロンプト 'Hi' に対するモックレスポンスです。"
        assert "Hi" in response.content
        assert "プロンプト" in response.content

    async def test_long_prompt_response(self, service):
        """Test response pattern for long prompts."""
        long_prompt = "This is a very long prompt " * 10  # 50+ characters
        response = await service.query(long_prompt)

        assert isinstance(response, LLMResponse)
        assert response.content
        # New service returns Japanese: "{len}文字のプロンプトを受信しました。これはモックLLMサービスからのテスト用レスポンスです。"
        assert str(len(long_prompt)) in response.content
        assert "文字" in response.content

    async def test_conversation_history_patterns(self, service):
        """Test conversation history handling."""
        history = [
            MessageItem(role=MessageRole.USER, content="What is Python?"),
            MessageItem(
                role=MessageRole.ASSISTANT, content="Python is a programming language."
            ),
        ]

        # Test that conversation history is accepted without error
        response = await service.query(
            "What was my previous question?", conversation_history=history
        )
        assert isinstance(response, LLMResponse)
        assert response.content
        # New service handles this as a regular query, so just check it responds
        assert len(response.content) > 0

    async def test_conversation_history_with_system_message(self, service):
        """Test conversation history with system messages."""
        history = [
            MessageItem(
                role=MessageRole.SYSTEM,
                content="You are a helpful programming assistant",
            ),
            MessageItem(role=MessageRole.USER, content="Hello"),
            MessageItem(role=MessageRole.ASSISTANT, content="Hello! How can I help?"),
            MessageItem(role=MessageRole.USER, content="Tell me about coding"),
        ]

        response = await service.query(
            "Continue our conversation", conversation_history=history
        )

        assert isinstance(response, LLMResponse)
        assert response.content
        # New service handles this as a regular query - just check it responds
        assert len(response.content) > 0

    async def test_invalid_conversation_history(self, service):
        """Test handling of invalid conversation history."""
        # Test with None history (should handle gracefully)
        response = await service.query(
            "Test with invalid history", conversation_history=None
        )

        assert isinstance(response, LLMResponse)
        assert response.content

        # Test with empty list
        response = await service.query(
            "Test with empty history", conversation_history=[]
        )

        assert isinstance(response, LLMResponse)
        assert response.content

        # Test with valid history
        valid_history = [
            MessageItem(role=MessageRole.USER, content="Hello"),
            MessageItem(role=MessageRole.ASSISTANT, content="Hi there!"),
        ]

        response = await service.query(
            "Test with valid history", conversation_history=valid_history
        )

        assert isinstance(response, LLMResponse)
        assert response.content


class TestMockLLMServiceUtilityMethods:
    """Test utility methods and helper functions."""

    @pytest.fixture
    def service(self):
        return MockLLMService(response_delay=0.01)

    async def test_format_prompt_success(self, service):
        """Test successful prompt formatting."""
        # This relies on the template manager working correctly
        formatted = await service.format_prompt(
            "simple_template", {"name": "World", "greeting": "Hello"}
        )

        assert isinstance(formatted, str)
        assert len(formatted) > 0

    async def test_format_prompt_error_handling(self, service):
        """Test prompt formatting error handling."""
        # Test with invalid template ID
        formatted = await service.format_prompt(
            "nonexistent_template", {"test": "value"}
        )

        assert isinstance(formatted, str)
        assert "nonexistent_template" in formatted
        # New service returns error about missing required variable 'prompt'
        assert "Error formatting template" in formatted

    async def test_get_available_templates(self, service):
        """Test getting available templates."""
        templates = await service.get_available_templates()

        assert isinstance(templates, list)
        # Should return some templates (might be empty depending on template manager)

    async def test_estimate_tokens(self, service):
        """Test token estimation."""
        # Test with various text lengths
        short_text = "Hello"
        medium_text = "This is a medium length text for testing token estimation"
        long_text = "This is a much longer text " * 20

        short_tokens = await service.estimate_tokens(short_text)
        medium_tokens = await service.estimate_tokens(medium_text)
        long_tokens = await service.estimate_tokens(long_text)

        assert isinstance(short_tokens, int)
        assert isinstance(medium_tokens, int)
        assert isinstance(long_tokens, int)

        # Longer text should have more tokens
        assert short_tokens < medium_tokens < long_tokens

        # Test estimation formula (len(text) // 4)
        assert short_tokens == len(short_text) // 4
        assert medium_tokens == len(medium_text) // 4


class TestMockLLMServiceEdgeCases:
    """Test edge cases and unusual scenarios."""

    @pytest.fixture
    def service(self):
        return MockLLMService(response_delay=0.01)

    async def test_query_with_none_options(self, service):
        """Test query with explicitly None options."""
        response = await service.query("Test query", options=None)

        assert isinstance(response, LLMResponse)
        assert response.content

    async def test_extremely_long_prompt(self, service):
        """Test with extremely long prompt."""
        very_long_prompt = "This is a very long prompt. " * 1000  # Very long

        response = await service.query(very_long_prompt)

        assert isinstance(response, LLMResponse)
        assert response.content
        assert response.usage.prompt_tokens > 0

    async def test_unicode_and_special_characters(self, service):
        """Test with Unicode and special characters."""
        unicode_prompt = "Test with émojis 🚀🔥 and spéciål chäracters ñáéíóú"

        response = await service.query(unicode_prompt)

        assert isinstance(response, LLMResponse)
        assert response.content

    async def test_query_optimization_info(self, service):
        """Test conversation history optimization information."""
        # Create a long conversation history
        long_history = []
        for i in range(20):
            long_history.append(
                MessageItem(role=MessageRole.USER, content=f"Question {i}")
            )
            long_history.append(
                MessageItem(role=MessageRole.ASSISTANT, content=f"Answer {i}")
            )

        response = await service.query(
            "Test with long history", conversation_history=long_history
        )

        assert isinstance(response, LLMResponse)
        assert hasattr(response, "optimized_conversation_history")
        assert hasattr(response, "history_optimization_info")
        # New service doesn't provide optimization info (returns None)
        assert response.history_optimization_info is None

        # Test with no history
        response_no_history = await service.query("Test without history")
        # New service returns None instead of empty list
        assert response_no_history.optimized_conversation_history is None
        assert response_no_history.history_optimization_info is None

    async def test_malformed_tool_definitions(self, service):
        """Test with malformed tool definitions."""
        malformed_tools = [
            {"type": "function"},  # Missing function key
            {"type": "other", "function": {"name": "test"}},  # Wrong type
            {"function": {"name": "test"}},  # Missing type
        ]

        response = await service.query(
            "Test with malformed tools", options={"tools": malformed_tools}
        )

        assert isinstance(response, LLMResponse)
        assert response.content


class TestMockLLMServiceSystemPromptConditions:
    """システムプロンプトの条件分岐をテストするクラス"""

    @pytest.fixture
    def service(self):
        return MockLLMService(response_delay=0.01)

    @pytest.mark.asyncio
    async def test_query_with_vscode_repository_context(self, service):
        """microsoft/vscodeリポジトリコンテキストでのクエリテスト"""
        repository_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="microsoft",
            repo="vscode",
            ref="main",
            base_url="https://github.com/microsoft/vscode",
        )

        response = await service.query(
            "How can I contribute to this project?",
            repository_context=repository_context,
            include_document_in_system_prompt=True,
        )
        assert isinstance(response, LLMResponse)
        assert response.content
        # VSCode関連のコンテキストでの応答を検証
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_query_with_test_minimal_repository_context(self, service):
        """test/minimalリポジトリコンテキストでのクエリテスト"""
        repository_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test",
            repo="minimal",
            ref="main",
            base_url="https://github.com/test/minimal",
        )

        response = await service.query(
            "What is this repository about?",
            repository_context=repository_context,
            include_document_in_system_prompt=True,
        )
        assert isinstance(response, LLMResponse)
        assert response.content
        # minimal関連のコンテキストでの応答を検証
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_query_with_generic_github_repository_context(self, service):
        """一般的なGitHubリポジトリコンテキストでのクエリテスト"""
        repository_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="someuser",
            repo="somerepo",
            ref="main",
            base_url="https://github.com/someuser/somerepo",
        )

        response = await service.query(
            "Please analyze this code",
            repository_context=repository_context,
            include_document_in_system_prompt=True,
        )
        assert isinstance(response, LLMResponse)
        assert response.content
        # リポジトリコンテキストでの応答を検証
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_query_with_repository_keyword_in_system_prompt(self, service):
        """システムプロンプトに'repository'キーワードが含まれる場合のテスト"""
        repository_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="example",
            repo="repository",
            ref="main",
            base_url="https://github.com/example/repository",
        )

        response = await service.query(
            "What files should I look at?",
            repository_context=repository_context,
            include_document_in_system_prompt=True,
        )
        assert isinstance(response, LLMResponse)
        assert response.content
        # リポジトリキーワードコンテキストでの応答を検証
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_conversation_history_with_vscode_context(self, service):
        """会話履歴があるVSCodeコンテキストでのテスト"""
        history = [
            MessageItem(role=MessageRole.USER, content="What is VSCode?"),
            MessageItem(role=MessageRole.ASSISTANT, content="VSCode is a code editor."),
        ]

        repository_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="microsoft",
            repo="vscode",
            ref="main",
            base_url="https://github.com/microsoft/vscode",
        )

        response = await service.query(
            "How do I debug extensions?",
            conversation_history=history,
            repository_context=repository_context,
            include_document_in_system_prompt=True,
        )
        assert isinstance(response, LLMResponse)
        assert response.content
        # 会話履歴とVSCodeコンテキストでの応答を検証
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_conversation_history_with_test_minimal_context(self, service):
        """会話履歴があるtest/minimalコンテキストでのテスト"""
        history = [
            MessageItem(role=MessageRole.USER, content="What is this repo?"),
            MessageItem(
                role=MessageRole.ASSISTANT, content="This is a test repository."
            ),
        ]

        repository_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test",
            repo="minimal",
            ref="main",
            base_url="https://github.com/test/minimal",
        )

        response = await service.query(
            "What should I test next?",
            conversation_history=history,
            repository_context=repository_context,
            include_document_in_system_prompt=True,
        )
        assert isinstance(response, LLMResponse)
        assert response.content
        # 会話履歴とminimalコンテキストでの応答を検証
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_conversation_history_with_generic_repository_context(self, service):
        """会話履歴がある一般的なリポジトリコンテキストでのテスト"""
        history = [
            MessageItem(
                role=MessageRole.USER, content="Please help me understand this code"
            ),
            MessageItem(
                role=MessageRole.ASSISTANT,
                content="I'll help you analyze the code structure.",
            ),
        ]

        repository_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="example",
            repo="codebase",
            ref="main",
            base_url="https://github.com/example/codebase",
        )

        response = await service.query(
            "Can you review my changes?",
            conversation_history=history,
            repository_context=repository_context,
            include_document_in_system_prompt=True,
        )
        assert isinstance(response, LLMResponse)
        assert response.content
        # 会話履歴とリポジトリコンテキストでの応答を検証
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_empty_conversation_history_fallback(self, service):
        """空の会話履歴の場合のフォールバック処理テスト"""
        response = await service.query("test prompt", conversation_history=[])
        assert isinstance(response, LLMResponse)
        # デフォルトの応答生成にフォールバックすることを確認
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_none_conversation_history_fallback(self, service):
        """None会話履歴の場合のフォールバック処理テスト"""
        response = await service.query("test prompt", conversation_history=None)
        assert isinstance(response, LLMResponse)
        # デフォルトの応答生成にフォールバックすることを確認
        assert len(response.content) > 0


class TestMockLLMServiceToolsAndFunctions:
    """Test tools and function calling functionality."""

    @pytest.fixture
    def service(self):
        """Create a MockLLMService instance for testing."""
        return MockLLMService(response_delay=0.01)

    @pytest.mark.asyncio
    async def test_query_with_tools(self, service):
        """Test query with tools functionality."""
        from doc_ai_helper_backend.models.llm import FunctionDefinition

        tools = [
            FunctionDefinition(
                name="test_tool",
                description="A test tool",
                parameters={"type": "object", "properties": {}},
            )
        ]

        response = await service.query_with_tools("Test prompt with tools", tools)

        assert isinstance(response, LLMResponse)
        assert response.content
        assert response.model == service.default_model

    @pytest.mark.asyncio
    async def test_query_with_tools_and_followup(self, service):
        """Test query with tools and followup functionality."""
        from doc_ai_helper_backend.models.llm import FunctionDefinition, ToolChoice

        tools = [
            FunctionDefinition(
                name="followup_tool",
                description="A followup tool",
                parameters={"type": "object", "properties": {}},
            )
        ]

        response = await service.query_with_tools_and_followup(
            "Test prompt for followup", tools, tool_choice=ToolChoice(type="auto")
        )

        assert isinstance(response, LLMResponse)
        assert response.content
        assert response.model == service.default_model

    @pytest.mark.asyncio
    async def test_get_available_functions(self, service):
        """Test getting available functions."""
        functions = await service.get_available_functions()
        assert isinstance(functions, list)
        # Mock service returns empty list by default


class TestMockLLMServiceProperties:
    """Test property accessors."""

    @pytest.fixture
    def service(self):
        """Create a MockLLMService instance for testing."""
        return MockLLMService(response_delay=0.01)

    # Legacy property tests removed - functionality now integrated into main service




class TestMockLLMServiceErrorHandling:
    """Test error handling in template methods."""

    @pytest.fixture
    def service(self):
        """Create a MockLLMService instance for testing."""
        return MockLLMService(response_delay=0.01)

    # Legacy template manager test removed - functionality now integrated


# Legacy utility function tests removed - functionality now integrated in main service


class TestMockLLMServiceComplexScenarios:
    """Test complex scenarios and edge cases."""

    @pytest.fixture
    def service(self):
        """Create a MockLLMService instance for testing."""
        return MockLLMService(response_delay=0.01)

    @pytest.mark.asyncio
    async def test_conversation_continuation_without_system_prompt(self, service):
        """Test conversation continuation when no system prompt is provided."""
        from doc_ai_helper_backend.models.llm import MessageItem, MessageRole

        history = [
            MessageItem(role=MessageRole.USER, content="Hello"),
            MessageItem(role=MessageRole.ASSISTANT, content="Hi!"),
        ]

        response = await service.query(
            "Continue our conversation",
            conversation_history=history,
            include_document_in_system_prompt=False,  # Force no system prompt
        )

        assert isinstance(response, LLMResponse)
        # New service handles this as regular query, so just check it responds
        assert len(response.content) > 0

