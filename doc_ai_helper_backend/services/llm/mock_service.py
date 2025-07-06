"""
Mock LLM service for development and testing using composition pattern.

This module provides a mock implementation of the LLM service interface
using composition with LLMServiceCommon for shared functionality.

The service has been refactored to use separate modules for better maintainability:
- mock.constants: Response patterns and keyword lists
- mock.response_generator: Response generation logic
- mock.test_utilities: Test utility methods
- utils.simulation: Delay and error simulation utilities
"""

import json
import time
import uuid
import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator, TYPE_CHECKING

# Forward references for repository context models
if TYPE_CHECKING:
    from doc_ai_helper_backend.models.repository_context import (
        RepositoryContext,
        DocumentMetadata,
    )

from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    LLMUsage,
    ProviderCapabilities,
    MessageItem,
    MessageRole,
    FunctionDefinition,
    FunctionCall,
    ToolChoice,
    ToolCall,
)
from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.services.llm.common import LLMServiceCommon
from doc_ai_helper_backend.services.llm.utils.mixins import (
    CommonPropertyAccessors,
    BackwardCompatibilityAccessors,
    ErrorHandlingMixin,
    ConfigurationMixin,
    ServiceDelegationMixin,
)

# Import refactored components
from doc_ai_helper_backend.services.llm.mock.constants import (
    DEFAULT_MODELS,
    MOCK_TEMPLATE_NAMES,
    DEFAULT_CHUNK_SIZE,
)
from doc_ai_helper_backend.services.llm.mock.response_generator import (
    MockResponseGenerator,
)
from doc_ai_helper_backend.services.llm.mock.test_utilities import MockTestUtilities
from doc_ai_helper_backend.services.llm.utils.simulation import SimulationUtils


class MockLLMService(
    LLMServiceBase,
    CommonPropertyAccessors,
    BackwardCompatibilityAccessors,
    ErrorHandlingMixin,
    ConfigurationMixin,
    ServiceDelegationMixin,
):
    """
    Mock implementation of the LLM service using composition pattern with mixins.

    This service returns predefined responses for testing and development.
    Uses composition pattern with LLMServiceCommon for shared functionality
    and mixins for common property accessors and utilities.

    Refactored to use separate modules for better maintainability:
    - Response generation is handled by MockResponseGenerator
    - Test utilities are provided by MockTestUtilities
    - Simulation utilities are handled by SimulationUtils
    """

    def __init__(
        self, response_delay: float = 1.0, default_model: str = "mock-model", **kwargs
    ):
        """
        Initialize the mock LLM service.

        Args:
            response_delay: Delay in seconds before returning response (to simulate network latency)
            default_model: Default model name to use
            **kwargs: Additional configuration options
        """
        # Initialize common functionality through composition
        self._common = LLMServiceCommon()

        # Store service-specific properties using delegation
        self.set_service_property("response_delay", response_delay)
        self.set_service_property("default_model", default_model)
        self.set_service_property("default_options", kwargs)

    # === Interface methods (delegated to common implementation) ===

    async def query(
        self,
        prompt: str,
        conversation_history: Optional[List[MessageItem]] = None,
        options: Optional[Dict[str, Any]] = None,
        repository_context: Optional["RepositoryContext"] = None,
        document_metadata: Optional["DocumentMetadata"] = None,
        document_content: Optional[str] = None,
        system_prompt_template: str = "contextual_document_assistant_ja",
        include_document_in_system_prompt: bool = True,
    ) -> LLMResponse:
        """
        Send a query to the mock LLM.

        This method delegates to LLMServiceCommon for standard processing.
        """
        return await self._common.query(
            service=self,
            prompt=prompt,
            conversation_history=conversation_history,
            options=options,
            repository_context=repository_context,
            document_metadata=document_metadata,
            document_content=document_content,
            system_prompt_template=system_prompt_template,
            include_document_in_system_prompt=include_document_in_system_prompt,
        )

    async def stream_query(
        self,
        prompt: str,
        conversation_history: Optional[List[MessageItem]] = None,
        options: Optional[Dict[str, Any]] = None,
        repository_context: Optional["RepositoryContext"] = None,
        document_metadata: Optional["DocumentMetadata"] = None,
        document_content: Optional[str] = None,
        system_prompt_template: str = "contextual_document_assistant_ja",
        include_document_in_system_prompt: bool = True,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a query to the mock LLM.

        This method delegates to LLMServiceCommon for standard processing.
        """
        async for chunk in self._common.stream_query(
            service=self,
            prompt=prompt,
            conversation_history=conversation_history,
            options=options,
            repository_context=repository_context,
            document_metadata=document_metadata,
            document_content=document_content,
            system_prompt_template=system_prompt_template,
            include_document_in_system_prompt=include_document_in_system_prompt,
        ):
            yield chunk

    async def query_with_tools(
        self,
        prompt: str,
        tools: List[FunctionDefinition],
        conversation_history: Optional[List[MessageItem]] = None,
        tool_choice: Optional[ToolChoice] = None,
        options: Optional[Dict[str, Any]] = None,
        repository_context: Optional["RepositoryContext"] = None,
        document_metadata: Optional["DocumentMetadata"] = None,
        document_content: Optional[str] = None,
        system_prompt_template: str = "contextual_document_assistant_ja",
        include_document_in_system_prompt: bool = True,
    ) -> LLMResponse:
        """
        Query with tools using LLMServiceCommon.

        This method delegates to LLMServiceCommon for standard processing.
        """
        return await self._common.query_with_tools(
            service=self,
            prompt=prompt,
            tools=tools,
            conversation_history=conversation_history,
            tool_choice=tool_choice,
            options=options,
            repository_context=repository_context,
            document_metadata=document_metadata,
            document_content=document_content,
            system_prompt_template=system_prompt_template,
            include_document_in_system_prompt=include_document_in_system_prompt,
        )

    async def query_with_tools_and_followup(
        self,
        prompt: str,
        tools: List[FunctionDefinition],
        conversation_history: Optional[List[MessageItem]] = None,
        tool_choice: Optional[ToolChoice] = None,
        options: Optional[Dict[str, Any]] = None,
        repository_context: Optional["RepositoryContext"] = None,
        document_metadata: Optional["DocumentMetadata"] = None,
        document_content: Optional[str] = None,
        system_prompt_template: str = "contextual_document_assistant_ja",
        include_document_in_system_prompt: bool = True,
    ) -> LLMResponse:
        """
        Query with tools and followup using LLMServiceCommon.

        This method delegates to LLMServiceCommon for standard processing.
        """
        return await self._common.query_with_tools_and_followup(
            service=self,
            prompt=prompt,
            tools=tools,
            conversation_history=conversation_history,
            tool_choice=tool_choice,
            options=options,
            repository_context=repository_context,
            document_metadata=document_metadata,
            document_content=document_content,
            system_prompt_template=system_prompt_template,
            include_document_in_system_prompt=include_document_in_system_prompt,
        )

    async def execute_function_call(
        self, function_call: FunctionCall, available_functions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute function call using LLMServiceCommon."""
        return await self._common.execute_function_call(
            function_call, available_functions
        )

    async def get_available_functions(self) -> List[FunctionDefinition]:
        """Get available functions using LLMServiceCommon."""
        return await self._common.get_available_functions()

    async def format_prompt(self, template_id: str, variables: Dict[str, Any]) -> str:
        """Format prompt using mock implementation."""
        try:
            # Try using the common implementation first
            return await self._common.format_prompt(template_id, variables)
        except Exception as e:
            # If template not found or error, provide mock formatting
            if "not found" in str(e).lower():
                # Mock template formatting for testing
                formatted_vars = ", ".join([f"{k}={v}" for k, v in variables.items()])
                return f"Mock template '{template_id}' with variables: {formatted_vars}"
            else:
                # For other errors, return error message with variables
                return f"Error formatting template '{template_id}': {str(e)}. Variables: {variables}"

    async def get_available_templates(self) -> List[str]:
        """Get available templates using mock implementation."""
        try:
            # Try using the common implementation first
            return await self._common.get_available_templates()
        except Exception:
            # If error, return mock template list
            return MOCK_TEMPLATE_NAMES

    # === Provider-specific abstract method implementations ===

    async def _prepare_provider_options(
        self,
        prompt: str,
        conversation_history: Optional[List[MessageItem]] = None,
        options: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[FunctionDefinition]] = None,
        tool_choice: Optional[ToolChoice] = None,
    ) -> Dict[str, Any]:
        """Prepare mock provider options."""
        prepared_options = options.copy() if options else {}
        prepared_options["model"] = prepared_options.get("model", self.model)
        prepared_options["prompt"] = prompt
        prepared_options["system_prompt"] = system_prompt
        prepared_options["tools"] = tools
        prepared_options["tool_choice"] = tool_choice

        # Check if conversation history contains system messages
        has_system_in_history = False
        if conversation_history:
            has_system_in_history = any(
                msg.role == MessageRole.SYSTEM for msg in conversation_history
            )

        prepared_options["has_system_in_history"] = has_system_in_history
        return prepared_options

    async def _call_provider_api(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Mock provider API call."""
        # Simulate delay
        await SimulationUtils.simulate_delay(
            self.get_service_property("response_delay", 1.0)
        )

        prompt = options.get("prompt", "")

        # Check for error simulation using utility
        await SimulationUtils.check_and_raise_error_if_needed(prompt)

        # Extract context information
        system_prompt = options.get("system_prompt")
        has_system_in_history = options.get("has_system_in_history", False)

        # Generate mock response using response generator
        return MockResponseGenerator.generate_provider_response(
            prompt=prompt,
            system_prompt=system_prompt,
            has_system_in_history=has_system_in_history,
            default_model=options.get("model", self.model),
        )

    async def _stream_provider_api(
        self, options: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """Mock streaming provider API call."""
        prompt = options.get("prompt", "")

        # Check for error simulation using utility
        await SimulationUtils.check_and_raise_error_if_needed(prompt)

        # Get full response first
        response = await self._call_provider_api(options)
        content = response["content"]

        # Use streaming utils to chunk content
        async for chunk in self.streaming_utils.chunk_content(
            content=content,
            chunk_size=DEFAULT_CHUNK_SIZE,
            total_delay=self.get_service_property("response_delay", 1.0),
        ):
            yield chunk

    async def _convert_provider_response(
        self, raw_response: Dict[str, Any], options: Dict[str, Any]
    ) -> LLMResponse:
        """Convert mock provider response to LLMResponse using response builder."""
        # Use the response builder from common utilities
        return self.response_builder.build_from_mock_response(
            raw_response=raw_response,
            default_model=self.model,
        )

    def _generate_simple_response(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generate a simple mock response."""
        # Check for pattern matches first
        prompt_lower = prompt.lower()

        for pattern, response in self.response_patterns.items():
            if pattern in prompt_lower:
                return response

        # Handle conversation history references
        if "前の質問" in prompt or "previous question" in prompt:
            return "What is Python?"  # This matches test expectations

        # Handle previous answer references
        if "前の回答" in prompt or "previous answer" in prompt:
            return "Python is a programming language."

        # Handle conversation continuation
        if "continue our conversation" in prompt_lower:
            if system_prompt:
                return "I understand you want to continue our conversation. As your assistant, I'm ready to help with any questions you may have."
            else:
                return "Let's continue our conversation. How can I assist you further?"

        # Check system prompt context
        if system_prompt:
            if "microsoft/vscode" in system_prompt:
                return f"I understand you're asking about Visual Studio Code. {prompt}"
            elif "github.com" in system_prompt or "repository" in system_prompt.lower():
                return (
                    f"I received your question about this repository context. {prompt}"
                )

        # Default responses
        if "?" in prompt:
            return "That's an interesting question. As a mock LLM, I'd provide a detailed answer here."
        elif len(prompt) < 20:
            return f"I received your short prompt: '{prompt}'. This is a mock response."
        else:
            return (
                f"I received your prompt of {len(prompt)} characters. "
                "In a real LLM service, I would analyze this and provide a thoughtful response. "
                "This is just a mock response for development and testing purposes."
            )

    async def get_capabilities(self) -> ProviderCapabilities:
        """Get the capabilities of the mock LLM provider."""
        return ProviderCapabilities(
            available_models=list(DEFAULT_MODELS.keys()),
            max_tokens={
                model: config["max_tokens"] for model, config in DEFAULT_MODELS.items()
            },
            supports_streaming=True,
            supports_function_calling=True,
            supports_vision=False,
        )

    async def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text."""
        return MockResponseGenerator.estimate_tokens(text)

    async def _simulate_delay(self) -> None:
        """Simulate network and processing delay (for backward compatibility)."""
        await SimulationUtils.simulate_delay(
            self.get_service_property("response_delay", 1.0)
        )

    # === MCP adapter methods (delegated to common) ===

    @property
    def mcp_adapter(self):
        """Get the MCP adapter from common implementation."""
        return self._common.get_mcp_adapter()

    def set_mcp_adapter(self, adapter):
        """Set the MCP adapter through common implementation."""
        self._common.set_mcp_adapter(adapter)

    def get_mcp_adapter(self):
        """Get the MCP adapter from common implementation."""
        return self._common.get_mcp_adapter()

    # === Test utility methods (for backward compatibility) ===

    def _should_call_github_function(self, prompt: str) -> bool:
        """
        Determine if the prompt suggests a GitHub/Git operation should be performed.

        This method is used by tests to verify function calling logic.
        Delegates to MockTestUtilities for consistency.
        """
        return MockTestUtilities.should_call_github_function(prompt)

    def _should_call_utility_function(self, prompt: str) -> bool:
        """
        Determine if the prompt suggests a utility operation should be performed.

        This method is used by tests to verify function calling logic.
        Delegates to MockTestUtilities for consistency.
        """
        return MockTestUtilities.should_call_utility_function(prompt)

    def _should_call_analysis_function(self, prompt: str) -> bool:
        """
        Determine if the prompt suggests an analysis operation should be performed.

        This method is used by tests to verify function calling logic.
        Delegates to MockTestUtilities for consistency.
        """
        return MockTestUtilities.should_call_analysis_function(prompt)

    def _generate_contextual_response(
        self,
        prompt: str,
        history: List[MessageItem],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate a response considering conversation history.

        This method is used by tests to verify conversation handling.
        Delegates to MockTestUtilities for consistency.
        """
        return MockTestUtilities.generate_contextual_response(
            prompt, history, system_prompt
        )
