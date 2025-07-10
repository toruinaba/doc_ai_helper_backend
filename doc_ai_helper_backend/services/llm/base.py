"""
Simplified base LLM service for composition pattern.

This module provides a minimal abstract base class for LLM services that works
with the composition pattern, avoiding multiple inheritance complexities.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncGenerator, TYPE_CHECKING

# Forward references for repository context models
if TYPE_CHECKING:
    from doc_ai_helper_backend.models.repository_context import (
        RepositoryContext,
        DocumentMetadata,
    )

from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    ProviderCapabilities,
    MessageItem,
    FunctionCall,
    FunctionDefinition,
    ToolCall,
    ToolChoice,
)


class LLMServiceBase(ABC):
    """
    Minimal base class for LLM services using composition pattern.

    This abstract class defines only the essential provider-specific methods
    that must be implemented by each LLM provider. Common functionality is
    handled by LLMServiceCommon through composition.
    """

    # === Provider-specific abstract methods (must be implemented by concrete classes) ===

    @abstractmethod
    async def get_capabilities(self) -> ProviderCapabilities:
        """
        Get the capabilities of the LLM provider.

        Returns:
            ProviderCapabilities: The capabilities of the provider
        """
        pass

    @abstractmethod
    async def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text.

        Args:
            text: The text to estimate tokens for

        Returns:
            int: Estimated token count
        """
        pass

    @abstractmethod
    async def _prepare_provider_options(
        self,
        prompt: str,
        conversation_history: Optional[List[MessageItem]] = None,
        options: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[FunctionDefinition]] = None,
        tool_choice: Optional[ToolChoice] = None,
    ) -> Dict[str, Any]:
        """
        Prepare provider-specific options for API call.

        This method converts standard parameters into the format required
        by the specific LLM provider's API.

        Args:
            prompt: The user prompt
            conversation_history: Previous messages in the conversation
            options: Additional options (model, temperature, etc.)
            system_prompt: Generated system prompt
            tools: Function definitions for tool calling
            tool_choice: Tool selection strategy

        Returns:
            Dict[str, Any]: Provider-specific options ready for API call
        """
        pass

    @abstractmethod
    async def _call_provider_api(self, options: Dict[str, Any]) -> Any:
        """
        Call the provider API with prepared options.

        This method makes the actual API call to the LLM provider.

        Args:
            options: Provider-specific options prepared by _prepare_provider_options

        Returns:
            Any: Raw response from the provider API
        """
        pass

    @abstractmethod
    async def _stream_provider_api(
        self, options: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """
        Stream from the provider API with prepared options.

        This method makes a streaming API call to the LLM provider.

        Args:
            options: Provider-specific options prepared by _prepare_provider_options

        Yields:
            str: Chunks of the response content
        """
        pass

    @abstractmethod
    async def _convert_provider_response(
        self, raw_response: Any, options: Dict[str, Any]
    ) -> LLMResponse:
        """
        Convert provider-specific response to standardized LLMResponse.

        This method converts the raw API response into our standard LLMResponse format.

        Args:
            raw_response: Raw response from the provider API
            options: Provider-specific options used for the API call

        Returns:
            LLMResponse: Standardized response object
        """
        pass

    # === Interface methods (delegated to common implementation) ===
    # These methods should be implemented by concrete classes to delegate to LLMServiceCommon

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
        Send a query to the LLM.

        This method should be implemented by concrete classes to delegate to LLMServiceCommon.
        """
        raise NotImplementedError(
            "Concrete classes must implement query method using LLMServiceCommon"
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
        Stream a query to the LLM.

        This method should be implemented by concrete classes to delegate to LLMServiceCommon.
        """
        raise NotImplementedError(
            "Concrete classes must implement stream_query method using LLMServiceCommon"
        )

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
        Send a query to the LLM with function calling tools.

        This method should be implemented by concrete classes to delegate to LLMServiceCommon.
        """
        raise NotImplementedError(
            "Concrete classes must implement query_with_tools method using LLMServiceCommon"
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
        Send a query to the LLM with function calling tools and handle the complete flow.

        This method should be implemented by concrete classes to delegate to LLMServiceCommon.
        """
        raise NotImplementedError(
            "Concrete classes must implement query_with_tools_and_followup method using LLMServiceCommon"
        )

    async def execute_function_call(
        self,
        function_call: FunctionCall,
        available_functions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a function call requested by the LLM.

        This method should be implemented by concrete classes to delegate to LLMServiceCommon.
        """
        raise NotImplementedError(
            "Concrete classes must implement execute_function_call method using LLMServiceCommon"
        )

    async def get_available_functions(self) -> List[FunctionDefinition]:
        """
        Get the list of available functions for this LLM service.

        This method should be implemented by concrete classes to delegate to LLMServiceCommon.
        """
        raise NotImplementedError(
            "Concrete classes must implement get_available_functions method using LLMServiceCommon"
        )

    async def format_prompt(self, template_id: str, variables: Dict[str, Any]) -> str:
        """
        Format a prompt template with variables.

        This method should be implemented by concrete classes to delegate to LLMServiceCommon.
        """
        raise NotImplementedError(
            "Concrete classes must implement format_prompt method using LLMServiceCommon"
        )

    async def get_available_templates(self) -> List[str]:
        """
        Get a list of available prompt template IDs.

        This method should be implemented by concrete classes to delegate to LLMServiceCommon.
        """
        raise NotImplementedError(
            "Concrete classes must implement get_available_templates method using LLMServiceCommon"
        )
