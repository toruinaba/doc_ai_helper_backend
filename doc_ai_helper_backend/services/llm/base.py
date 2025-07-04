"""
Base LLM service.

This module provides the base abstract class for LLM services.
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
    # Function Calling関連のモデルを追加
    FunctionCall,
    FunctionDefinition,
    ToolCall,
    ToolChoice,
)


class LLMServiceBase(ABC):
    """
    Base class for LLM services.

    This abstract class defines the interface that all LLM service implementations
    must follow. It provides methods for querying LLMs, retrieving capabilities,
    and formatting prompts.
    """

    @abstractmethod
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

        Args:
            prompt: The prompt to send to the LLM
            conversation_history: Previous messages in the conversation for context
            options: Additional options for the query (model, temperature, etc.)
            repository_context: Repository context for system prompt generation
            document_metadata: Document metadata for context
            document_content: Document content to include in system prompt
            system_prompt_template: Template ID for system prompt generation
            include_document_in_system_prompt: Whether to include document content

        Returns:
            LLMResponse: The response from the LLM
        """
        pass

    @abstractmethod
    async def get_capabilities(self) -> ProviderCapabilities:
        """
        Get the capabilities of the LLM provider.        Returns:
            ProviderCapabilities: The capabilities of the provider
        """
        pass

    @abstractmethod
    async def format_prompt(self, template_id: str, variables: Dict[str, Any]) -> str:
        """
        Format a prompt template with variables.

        Args:
            template_id: The ID of the template to use
            variables: The variables to substitute in the template

        Returns:
            str: The formatted prompt
        """
        pass

    @abstractmethod
    async def get_available_templates(self) -> List[str]:
        """
        Get a list of available prompt template IDs.

        Returns:
            List[str]: List of template IDs
        """
        pass

    @abstractmethod
    async def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text.

        Args:
            text: The text to estimate tokens for        Returns:
            int: Estimated token count
        """
        pass

    @abstractmethod
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

        Args:
            prompt: The prompt to send to the LLM
            conversation_history: Previous messages in the conversation for context
            options: Additional options for the query (model, temperature, etc.)
            repository_context: Repository context for system prompt generation
            document_metadata: Document metadata for context
            document_content: Document content to include in system prompt
            system_prompt_template: Template ID for system prompt generation
            include_document_in_system_prompt: Whether to include document content

        Returns:
            AsyncGenerator[str, None]: An async generator that yields chunks of the response
        """
        pass

    @abstractmethod
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

        Args:
            prompt: The prompt to send to the LLM
            tools: List of available function definitions
            conversation_history: Previous messages in the conversation for context
            tool_choice: Strategy for tool selection (auto, none, required, or specific function)
            options: Additional options for the query (model, temperature, etc.)
            repository_context: Repository context for system prompt generation
            document_metadata: Document metadata for context
            document_content: Document content to include in system prompt
            system_prompt_template: Template ID for system prompt generation
            include_document_in_system_prompt: Whether to include document content

        Returns:
            LLMResponse: The response from the LLM, potentially including tool calls
        """
        pass

    @abstractmethod
    async def execute_function_call(
        self,
        function_call: FunctionCall,
        available_functions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a function call requested by the LLM.

        Args:
            function_call: The function call details from the LLM
            available_functions: Dictionary of available functions to call

        Returns:
            Dict[str, Any]: The result of the function execution
        """
        pass

    @abstractmethod
    async def get_available_functions(self) -> List[FunctionDefinition]:
        """
        Get the list of available functions for this LLM service.

        Returns:
            List[FunctionDefinition]: List of available function definitions
        """
        pass

    @abstractmethod
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

        This method implements the complete Function Calling flow:
        1. Send initial query with tools
        2. If LLM calls tools, execute them
        3. Send tool results back to LLM for final response

        Args:
            prompt: The prompt to send to the LLM
            tools: List of available function definitions
            conversation_history: Previous messages in the conversation for context
            tool_choice: Strategy for tool selection
            options: Additional options for the query
            repository_context: Repository context for system prompt generation
            document_metadata: Document metadata for context
            document_content: Document content to include in system prompt
            system_prompt_template: Template ID for system prompt generation
            include_document_in_system_prompt: Whether to include document content

        Returns:
            LLMResponse: The final response from the LLM after tool execution
        """
        pass

    def build_system_prompt_with_context(
        self,
        repository_context: Optional["RepositoryContext"] = None,
        document_metadata: Optional["DocumentMetadata"] = None,
        document_content: Optional[str] = None,
        template_id: str = "contextual_document_assistant_ja",
    ) -> Optional[str]:
        """
        Build system prompt with repository and document context.

        This method provides a default implementation that can be overridden
        by specific LLM service implementations.

        Args:
            repository_context: Repository context information
            document_metadata: Document metadata
            document_content: Document content to include in prompt
            template_id: Template identifier for prompt generation

        Returns:
            Generated system prompt or None if context is insufficient
        """
        # Default implementation - can be overridden by subclasses
        if not repository_context:
            return None

        # Basic template without specialized prompt builder
        return f"""あなたは {repository_context.owner}/{repository_context.repo} リポジトリを扱うアシスタントです。

現在作業中のリポジトリ: {repository_context.owner}/{repository_context.repo}

GitHubツールを使用する際は、特に指定がない限り自動的に "{repository_context.owner}/{repository_context.repo}" リポジトリを使用してください。"""
