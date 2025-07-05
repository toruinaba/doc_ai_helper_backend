"""
OpenAI LLM service.

This module provides an implementation of the LLM service using OpenAI's API.
It can be used with OpenAI directly or with a LiteLLM proxy server.

This service has been refactored to use separate modules for different responsibilities:
- openai_client: API communication
- openai_options_builder: Options preparation
- openai_response_converter: Response conversion
- openai_function_handler: Function calling operations
"""

import logging
from typing import Dict, Any, Optional, List, AsyncGenerator, TYPE_CHECKING

import tiktoken

# Forward references for repository context models
if TYPE_CHECKING:
    from doc_ai_helper_backend.models.repository_context import (
        RepositoryContext,
        DocumentMetadata,
    )

from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.services.llm.template_manager import PromptTemplateManager
from doc_ai_helper_backend.services.llm.cache_service import LLMCacheService
from doc_ai_helper_backend.services.llm.legacy.openai_client import OpenAIAPIClient
from doc_ai_helper_backend.services.llm.legacy.openai_options_builder import (
    OpenAIOptionsBuilder,
)
from doc_ai_helper_backend.services.llm.legacy.openai_response_converter import (
    OpenAIResponseConverter,
)
from doc_ai_helper_backend.services.llm.legacy.openai_function_handler import (
    OpenAIFunctionHandler,
)
from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    ProviderCapabilities,
    MessageItem,
    FunctionDefinition,
    ToolChoice,
)
from doc_ai_helper_backend.core.exceptions import (
    LLMServiceException,
    TemplateNotFoundError,
    TemplateSyntaxError,
)

logger = logging.getLogger(__name__)


class OpenAIService(LLMServiceBase):
    """
    OpenAI implementation of the LLM service.

    This service uses OpenAI's API to provide LLM functionality.
    It can be configured to use OpenAI directly or a LiteLLM proxy server.

    This service has been refactored for better maintainability:
    - Uses OpenAIAPIClient for API communication
    - Uses OpenAIOptionsBuilder for options preparation
    - Uses OpenAIResponseConverter for response conversion
    - Uses OpenAIFunctionHandler for function calling operations
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = "gpt-3.5-turbo",
        base_url: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the OpenAI service.

        Args:
            api_key: The OpenAI API key or proxy server API key
            default_model: The default model to use
            base_url: Optional base URL for the API (e.g., LiteLLM proxy URL)
            **kwargs: Additional configuration options
        """
        self.api_key = api_key
        self.default_model = default_model
        self.base_url = base_url
        self.additional_options = kwargs

        # Initialize core components
        self.template_manager = PromptTemplateManager()
        self.cache_service = LLMCacheService()

        # Initialize specialized components
        self.api_client = OpenAIAPIClient(api_key, base_url)
        self.options_builder = OpenAIOptionsBuilder(default_model)
        self.response_converter = OpenAIResponseConverter()

        # Initialize system prompt builder
        from doc_ai_helper_backend.services.llm.system_prompt_builder import (
            JapaneseSystemPromptBuilder,
        )

        self.system_prompt_builder = JapaneseSystemPromptBuilder()

        # Initialize MCP integration
        self._mcp_adapter = self._initialize_mcp_adapter()

        # Initialize function handler
        self.function_handler = OpenAIFunctionHandler(
            self.api_client,
            self.response_converter,
            self.options_builder,
            self._mcp_adapter,
        )

        # Load token encoder for the default model
        try:
            self._token_encoder = tiktoken.encoding_for_model(default_model)
        except KeyError:
            # Fall back to a common encoding if model-specific one is not available
            self._token_encoder = tiktoken.get_encoding("cl100k_base")

        logger.info(
            f"Initialized OpenAIService with default model {default_model}"
            f"{' and custom base URL' if base_url else ''}"
        )

    @property
    def async_client(self):
        """Backward compatibility property for tests."""
        return self.api_client.async_client

    @async_client.setter
    def async_client(self, value):
        """Backward compatibility setter for tests."""
        self.api_client.async_client = value

    @property
    def sync_client(self):
        """Backward compatibility property for tests."""
        return self.api_client.sync_client

    @sync_client.setter
    def sync_client(self, value):
        """Backward compatibility setter for tests."""
        self.api_client.sync_client = value

    def _prepare_options(
        self,
        prompt: str,
        options: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[MessageItem]] = None,
    ) -> Dict[str, Any]:
        """Backward compatibility method for tests."""
        return self.options_builder.prepare_options(
            prompt, options or {}, conversation_history
        )

    def _convert_to_llm_response(self, response, model: str) -> LLMResponse:
        """Backward compatibility method for tests."""
        return self.response_converter.convert_to_llm_response(response, model)

    def _initialize_mcp_adapter(self):
        """Initialize MCP adapter if available."""
        try:
            from doc_ai_helper_backend.services.mcp.function_adapter import (
                MCPFunctionAdapter,
            )
            from doc_ai_helper_backend.services.mcp.server import (
                DocumentAIHelperMCPServer,
            )

            mcp_server = DocumentAIHelperMCPServer()
            return MCPFunctionAdapter(mcp_server)
        except ImportError as e:
            logger.warning(f"MCP adapter not available: {e}")
            return None

    async def query(
        self,
        prompt: str,
        conversation_history: Optional[List["MessageItem"]] = None,
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
            conversation_history: Previous messages in the conversation
            options: Additional options for the query (model, temperature, etc.)
            repository_context: Repository context for system prompt generation
            document_metadata: Document metadata for context
            document_content: Document content to include in system prompt
            system_prompt_template: Template ID for system prompt generation
            include_document_in_system_prompt: Whether to include document content

        Returns:
            LLMResponse: The response from the LLM
        """
        options = options or {}

        # Generate system prompt with context if repository context is provided
        system_prompt = self._generate_system_prompt(
            repository_context,
            document_metadata,
            document_content,
            system_prompt_template,
            include_document_in_system_prompt,
        )

        # Prepare query options using the options builder
        query_options = self.options_builder.prepare_options(
            prompt, options, conversation_history, system_prompt=system_prompt
        )
        model = query_options.get("model", self.default_model)

        # Handle caching
        disable_cache = query_options.pop("disable_cache", False)
        cache_key = None

        if not disable_cache:
            cache_key = self.cache_service.generate_key(prompt, query_options)
            cached_response = self.cache_service.get(cache_key)
            if cached_response:
                logger.debug(f"Cache hit for prompt with key {cache_key[:8]}")
                return cached_response
        else:
            logger.debug("Cache disabled for this request")

        try:
            # Call OpenAI API using the client
            logger.debug(f"Sending query to OpenAI with model {model}")
            response = await self.api_client.call_api(query_options)

            # Convert OpenAI response to LLMResponse using the converter
            llm_response = self.response_converter.convert_to_llm_response(
                response, model
            )

            # Handle conversation history optimization
            self._handle_conversation_optimization(llm_response, conversation_history)

            # Cache the response (if caching is not disabled)
            if not disable_cache and cache_key:
                self.cache_service.set(cache_key, llm_response)

            return llm_response

        except Exception as e:
            logger.error(f"Error querying OpenAI: {str(e)}")
            raise LLMServiceException(message=f"Error querying OpenAI: {str(e)}")

    def _generate_system_prompt(
        self,
        repository_context: Optional["RepositoryContext"],
        document_metadata: Optional["DocumentMetadata"],
        document_content: Optional[str],
        system_prompt_template: str,
        include_document_in_system_prompt: bool,
    ) -> Optional[str]:
        """Generate system prompt if repository context is provided."""
        if not repository_context or not include_document_in_system_prompt:
            return None

        try:
            system_prompt = self.system_prompt_builder.build_system_prompt(
                repository_context=repository_context,
                document_metadata=document_metadata,
                document_content=document_content,
                template_id=system_prompt_template,
            )
            logger.info(
                f"Generated system prompt with template: {system_prompt_template}"
            )
            return system_prompt
        except Exception as e:
            logger.warning(
                f"Failed to generate system prompt: {e}, falling back to minimal context"
            )
            return self._create_fallback_system_prompt(
                repository_context=repository_context
            )

    def _handle_conversation_optimization(
        self,
        llm_response: LLMResponse,
        conversation_history: Optional[List["MessageItem"]],
    ) -> None:
        """Handle conversation history optimization."""
        # Import here to avoid circular imports
        from doc_ai_helper_backend.services.llm.utils import (
            optimize_conversation_history,
        )

        if conversation_history:
            optimized_history, optimization_info = optimize_conversation_history(
                conversation_history, max_tokens=4000
            )
            llm_response.optimized_conversation_history = optimized_history
            llm_response.history_optimization_info = optimization_info
        else:
            llm_response.optimized_conversation_history = []
            llm_response.history_optimization_info = {
                "was_optimized": False,
                "reason": "No conversation history provided",
            }

    async def get_capabilities(self) -> ProviderCapabilities:
        """
        Get the capabilities of the OpenAI provider.

        Returns:
            ProviderCapabilities: The capabilities of the provider
        """
        # Define available models - This is a simplified list, in a real implementation
        # you might want to fetch this from the OpenAI API
        available_models = [
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-32k",
        ]

        # Define max tokens for each model
        max_tokens = {
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-4-32k": 32768,
        }

        # Return capabilities
        return ProviderCapabilities(
            available_models=available_models,
            max_tokens=max_tokens,
            supports_streaming=True,
            supports_function_calling=True,
            supports_vision=True,
        )

    async def format_prompt(self, template_id: str, variables: Dict[str, Any]) -> str:
        """
        Format a prompt template with variables.

        Args:
            template_id: The ID of the template to use
            variables: The variables to substitute in the template

        Returns:
            str: The formatted prompt
        """
        try:
            return self.template_manager.format_template(template_id, variables)
        except (TemplateNotFoundError, TemplateSyntaxError) as e:
            logger.error(f"Error formatting prompt template: {str(e)}")
            raise

    async def get_available_templates(self) -> List[str]:
        """
        Get a list of available prompt template IDs.

        Returns:
            List[str]: List of template IDs
        """
        return self.template_manager.list_templates()

    async def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text.

        Args:
            text: The text to estimate tokens for

        Returns:
            int: Estimated token count
        """
        return len(self._token_encoder.encode(text))

    def _create_fallback_system_prompt(
        self, repository_context: Optional["RepositoryContext"] = None
    ) -> str:
        """
        Create a minimal fallback system prompt.

        Args:
            repository_context: Repository context information

        Returns:
            str: Minimal system prompt
        """
        if repository_context:
            return (
                f"あなたは{repository_context.repository_full_name}リポジトリの"
                f"ドキュメントアシスタントです。"
                f"ユーザーの質問に対して、提供されたコンテキストを基に回答してください。"
            )
        else:
            return "あなたは親切なアシスタントです。ユーザーの質問に回答してください。"

    async def stream_query(
        self,
        prompt: str,
        conversation_history: Optional[List["MessageItem"]] = None,
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
            conversation_history: Previous messages in the conversation
            options: Additional options for the query (model, temperature, etc.)
            repository_context: Repository context for system prompt generation
            document_metadata: Document metadata for context
            document_content: Document content to include in system prompt
            system_prompt_template: Template ID for system prompt generation
            include_document_in_system_prompt: Whether to include document content

        Returns:
            AsyncGenerator[str, None]: An async generator that yields chunks of the response
        """
        options = options or {}

        # Generate system prompt
        system_prompt = self._generate_system_prompt(
            repository_context,
            document_metadata,
            document_content,
            system_prompt_template,
            include_document_in_system_prompt,
        )

        # Prepare options using the options builder
        query_options = self.options_builder.prepare_options(
            prompt, options, conversation_history, system_prompt=system_prompt
        )

        try:
            # Stream using the API client
            async for chunk in self.api_client.stream_api(query_options):
                yield chunk

        except Exception as e:
            logger.error(f"Error in streaming query: {str(e)}")
            raise LLMServiceException(f"Streaming error: {str(e)}")

    def set_mcp_adapter(self, mcp_adapter) -> None:
        """
        Set MCP adapter for function calling integration.

        Args:
            mcp_adapter: MCP function adapter instance
        """
        self._mcp_adapter = mcp_adapter
        # Update the function handler with the new adapter
        self.function_handler = OpenAIFunctionHandler(
            self.api_client, self.response_converter, self.options_builder, mcp_adapter
        )
        if mcp_adapter:
            logger.info("MCP adapter configured for OpenAI service")

    async def query_with_tools(
        self,
        prompt: str,
        tools: List["FunctionDefinition"],
        conversation_history: Optional[List["MessageItem"]] = None,
        tool_choice: Optional["ToolChoice"] = None,
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
            tool_choice: Strategy for tool selection
            options: Additional options for the query
            repository_context: Repository context for secure tools
            document_metadata: Document metadata for context
            document_content: Document content for context
            system_prompt_template: Template ID for system prompt
            include_document_in_system_prompt: Whether to include document in system prompt

        Returns:
            LLMResponse: The response from the LLM, potentially including tool calls
        """
        return await self.function_handler.query_with_tools(
            prompt=prompt,
            tools=tools,
            conversation_history=conversation_history,
            options=options,
            tool_choice=tool_choice,
            repository_context=repository_context,
            document_metadata=document_metadata,
            document_content=document_content,
            system_prompt_template=system_prompt_template,
            include_document_in_system_prompt=include_document_in_system_prompt,
        )

    async def query_with_tools_and_followup(
        self,
        prompt: str,
        tools: List["FunctionDefinition"],
        conversation_history: Optional[List["MessageItem"]] = None,
        tool_choice: Optional["ToolChoice"] = None,
        options: Optional[Dict[str, Any]] = None,
        max_iterations: int = 3,
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
            conversation_history: Previous messages in the conversation
            tool_choice: Strategy for tool selection
            options: Additional options for the query
            max_iterations: Maximum number of tool call iterations
            repository_context: Repository context for secure tools
            document_metadata: Document metadata for context
            document_content: Document content for context
            system_prompt_template: Template ID for system prompt
            include_document_in_system_prompt: Whether to include document in system prompt

        Returns:
            LLMResponse: The final response after tool execution
        """
        return await self.function_handler.query_with_tools_and_followup(
            prompt=prompt,
            tools=tools,
            conversation_history=conversation_history,
            options=options,
            tool_choice=tool_choice,
            max_iterations=max_iterations,
            repository_context=repository_context,
            document_metadata=document_metadata,
            document_content=document_content,
            system_prompt_template=system_prompt_template,
            include_document_in_system_prompt=include_document_in_system_prompt,
        )

    async def get_available_functions(self) -> List["FunctionDefinition"]:
        """
        Get available functions from MCP adapter.

        Returns:
            List[FunctionDefinition]: Available functions
        """
        return await self.function_handler.get_available_functions()

    async def execute_function_call(
        self, function_name: str, arguments: str
    ) -> Dict[str, Any]:
        """
        Execute a function call using the MCP adapter.

        Args:
            function_name: Name of the function to call
            arguments: JSON string of function arguments

        Returns:
            Dict[str, Any]: The result of the function call
        """
        return await self.function_handler.execute_function_call(
            function_name, arguments
        )

    # Additional LLMServiceBase methods
    async def get_capabilities(self) -> ProviderCapabilities:
        """
        Get the capabilities of the OpenAI provider.

        Returns:
            ProviderCapabilities: The capabilities of the provider
        """
        # Define available models - This is a simplified list
        available_models = [
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-4",
            "gpt-4-32k",
            "gpt-4-turbo-preview",
            "gpt-4o",
            "gpt-4o-mini",
        ]

        # Define max tokens for each model
        max_tokens = {
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-4-turbo-preview": 128000,
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
        }

        return ProviderCapabilities(
            available_models=available_models,
            max_tokens=max_tokens,
            supports_streaming=True,
            supports_function_calling=True,
            supports_vision=True,
        )

    async def format_prompt(self, template_id: str, variables: Dict[str, Any]) -> str:
        """
        Format a prompt template with variables.

        Args:
            template_id: The ID of the template to use
            variables: Variables to substitute in the template

        Returns:
            str: The formatted prompt

        Raises:
            TemplateNotFoundError: If template is not found
            TemplateSyntaxError: If template formatting fails
        """
        return await self.template_manager.format_template(template_id, variables)

    async def get_available_templates(self) -> List[str]:
        """
        Get available prompt templates.

        Returns:
            List[str]: List of template IDs
        """
        return self.template_manager.get_available_templates()

    async def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text.

        Args:
            text: The text to estimate tokens for

        Returns:
            int: Estimated token count
        """
        return len(self._token_encoder.encode(text))

    def _create_fallback_system_prompt(
        self, repository_context: Optional["RepositoryContext"] = None
    ) -> str:
        """
        Create a minimal fallback system prompt.

        Args:
            repository_context: Repository context information

        Returns:
            str: Minimal system prompt
        """
        if repository_context:
            return (
                f"あなたは{repository_context.repository_full_name}リポジトリの"
                f"ドキュメントアシスタントです。"
                f"ユーザーの質問に対して、提供されたコンテキストを基に回答してください。"
            )
        else:
            return "あなたは親切なアシスタントです。ユーザーの質問に回答してください。"
