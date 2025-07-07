"""
OpenAI LLM service using pure delegation pattern.

This module provides an implementation of the LLM service using OpenAI's API
with pure delegation pattern to individual components for maximum modularity and testability.
"""

import logging
from typing import Dict, Any, Optional, List, AsyncGenerator, TYPE_CHECKING

import tiktoken
from openai import OpenAI, AsyncOpenAI

# Forward references for repository context models
if TYPE_CHECKING:
    from doc_ai_helper_backend.models.repository_context import (
        RepositoryContext,
        DocumentMetadata,
    )

from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    LLMUsage,
    ProviderCapabilities,
    MessageItem,
    MessageRole,
    FunctionDefinition,
    ToolChoice,
    ToolCall,
    FunctionCall,
)
from doc_ai_helper_backend.core.exceptions import (
    LLMServiceException,
)

logger = logging.getLogger(__name__)


class OpenAIService(LLMServiceBase):
    """
    OpenAI implementation of the LLM service using pure delegation pattern.

    This service uses OpenAI's API to provide LLM functionality.
    All shared functionality is delegated to individual component instances.
    It can be configured to use OpenAI directly or a LiteLLM proxy server.
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
        # Initialize components directly using pure composition
        from doc_ai_helper_backend.services.llm.processing.templates import (
            PromptTemplateManager,
        )
        from doc_ai_helper_backend.services.llm.processing.cache import LLMCacheService
        from doc_ai_helper_backend.services.llm.messaging.messaging import (
            SystemPromptBuilder,
        )
        from doc_ai_helper_backend.services.llm.functions.functions import (
            FunctionCallManager,
        )
        from doc_ai_helper_backend.services.llm.processing.response_builder import (
            ResponseBuilder,
        )
        from doc_ai_helper_backend.services.llm.processing.streaming_utils import (
            StreamingUtils,
        )
        from doc_ai_helper_backend.services.llm.query_manager import QueryManager

        # Direct component composition - no intermediate layer
        self.template_manager = PromptTemplateManager()
        self.cache_service = LLMCacheService()
        self.system_prompt_builder = SystemPromptBuilder()
        self.function_manager = FunctionCallManager()
        self.response_builder = ResponseBuilder()
        self.streaming_utils = StreamingUtils()

        # Query manager with dependency injection
        self.query_manager = QueryManager(
            cache_service=self.cache_service,
            system_prompt_builder=self.system_prompt_builder,
        )

        # Store service-specific properties using delegation
        self.set_service_property("api_key", api_key)
        self.set_service_property("default_model", default_model)
        self.set_service_property("base_url", base_url)
        self.set_service_property("default_options", kwargs)

        # Initialize MCP adapter as None (can be set later)
        self._mcp_adapter = None

        self._initialize_clients_and_encoder()

        logger.info(
            f"Initialized OpenAIService with default model {default_model}"
            f"{' and custom base URL' if base_url else ''}"
        )

    def set_service_property(self, property_name: str, value):
        """Set a service-specific property."""
        setattr(self, f"_{property_name}", value)

    def get_service_property(self, property_name: str, default=None):
        """Get a service-specific property."""
        return getattr(self, f"_{property_name}", default)

    # === Property delegation for backward compatibility ===

    @property
    def api_key(self) -> str:
        """Access to API key."""
        return self.get_service_property("api_key")

    @property
    def model(self) -> str:
        """Access to default model."""
        return self.get_service_property("default_model")

    @property
    def base_url(self) -> Optional[str]:
        """Access to base URL."""
        return self.get_service_property("base_url")

    @property
    def default_options(self) -> Dict[str, Any]:
        """Access to default options."""
        return self.get_service_property("default_options", {})

    # === Component access properties (direct access, no intermediate layer) ===

    @property
    def function_handler(self):
        """Access to function manager (backward compatibility alias)."""
        return self.function_manager

    # === MCP adapter methods ===

    @property
    def mcp_adapter(self):
        """Get the MCP adapter."""
        return self._mcp_adapter

    def set_mcp_adapter(self, adapter):
        """Set the MCP adapter."""
        self._mcp_adapter = adapter

    def get_mcp_adapter(self):
        """Get the MCP adapter."""
        return self._mcp_adapter

    # === Service initialization and client management ===

    def _initialize_clients_and_encoder(self):
        """Initialize OpenAI clients and token encoder."""
        # Initialize OpenAI clients
        client_params = {"api_key": self.get_service_property("api_key")}
        if self.get_service_property("base_url"):
            client_params["base_url"] = self.get_service_property("base_url")

        self.sync_client = OpenAI(**client_params)
        self.async_client = AsyncOpenAI(**client_params)

        # Load token encoder for the default model
        try:
            self._token_encoder = tiktoken.encoding_for_model(
                self.get_service_property("default_model")
            )
        except KeyError:
            # Fall back to a common encoding if model-specific one is not available
            self._token_encoder = tiktoken.get_encoding("cl100k_base")

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
        """Direct delegation to query manager."""
        return await self.query_manager.orchestrate_query(
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
        """Direct delegation to query manager."""
        async for chunk in self.query_manager.orchestrate_streaming_query(
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
        """Direct delegation to query manager."""
        return await self.query_manager.orchestrate_query_with_tools(
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
        """Direct delegation to query manager."""
        return await self.query_manager.orchestrate_query_with_tools(
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
        self,
        function_call: FunctionCall,
        available_functions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Direct delegation to function manager."""
        return await self.function_manager.execute_function_call(
            function_call, available_functions
        )

    async def get_available_functions(self) -> List[FunctionDefinition]:
        """Direct delegation to function manager."""
        return self.function_manager.get_available_functions()

    async def format_prompt(self, template_id: str, variables: Dict[str, Any]) -> str:
        """Direct delegation to template manager."""
        return self.template_manager.format_template(template_id, variables)

    async def get_available_templates(self) -> List[str]:
        """Direct delegation to template manager."""
        return self.template_manager.list_templates()

    # === Provider-specific implementations ===

    async def get_capabilities(self) -> ProviderCapabilities:
        """
        Get the capabilities of the OpenAI provider.
        """
        return ProviderCapabilities(
            provider="openai",
            available_models=[
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-16k",
                "gpt-4",
                "gpt-4-turbo",
                "gpt-4o",
                "gpt-4o-mini",
            ],
            max_tokens={
                "gpt-3.5-turbo": 4096,
                "gpt-3.5-turbo-16k": 16384,
                "gpt-4": 8192,
                "gpt-4-turbo": 128000,
                "gpt-4o": 128000,
                "gpt-4o-mini": 128000,
            },
            supports_streaming=True,
            supports_function_calling=True,
        )

    async def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text using OpenAI's tiktoken.
        """
        try:
            return len(self._token_encoder.encode(text))
        except Exception as e:
            logger.warning(
                f"Failed to estimate tokens: {str(e)}, using character approximation"
            )
            return len(text) // 4

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
        Prepare OpenAI-specific options for API call.
        """
        options = options or {}

        # Build conversation messages in standard format
        messages = self.query_manager.build_conversation_messages(
            prompt, conversation_history, system_prompt
        )

        # Convert to OpenAI format
        openai_messages = []
        for msg in messages:
            openai_msg = {"role": msg.role.value, "content": msg.content}

            # Handle tool calls for assistant messages (if tool_calls attribute exists)
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                openai_msg["tool_calls"] = []
                for tool_call in msg.tool_calls:
                    openai_msg["tool_calls"].append(
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                    )

            # Handle tool call ID for tool messages (if tool_call_id attribute exists)
            if hasattr(msg, "tool_call_id") and msg.tool_call_id:
                openai_msg["tool_call_id"] = msg.tool_call_id

            openai_messages.append(openai_msg)

        # Prepare OpenAI-specific options
        provider_options = {
            "model": options.get("model", self.model),
            "messages": openai_messages,
            "temperature": options.get("temperature", 0.7),
            "max_tokens": options.get("max_tokens", 1000),
        }

        # Handle tools/functions
        if tools:
            provider_options["tools"] = self._convert_tools_to_openai_format(tools)

            if tool_choice:
                provider_options["tool_choice"] = (
                    self._convert_tool_choice_to_openai_format(tool_choice)
                )

        # Add any additional options (excluding processed ones)
        excluded_keys = {"model", "tools", "tool_choice", "temperature", "max_tokens"}
        for key, value in options.items():
            if key not in excluded_keys:
                provider_options[key] = value

        logger.info(f"Prepared OpenAI options with model: {provider_options['model']}")
        return provider_options

    async def _call_provider_api(self, options: Dict[str, Any]) -> Any:
        """
        Call the OpenAI API with prepared options.
        """
        try:
            response = await self.async_client.chat.completions.create(**options)
            logger.info(f"OpenAI API call successful, model: {response.model}")
            return response
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise LLMServiceException(f"OpenAI API call failed: {str(e)}")

    async def _stream_provider_api(
        self, options: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """
        Stream from the OpenAI API with prepared options.
        """
        try:
            # Enable streaming
            options["stream"] = True

            stream = await self.async_client.chat.completions.create(**options)

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming API call failed: {str(e)}")
            raise LLMServiceException(f"OpenAI streaming failed: {str(e)}")

    async def _convert_provider_response(
        self, raw_response: Any, options: Dict[str, Any]
    ) -> LLMResponse:
        """
        Convert OpenAI response to standardized LLMResponse using response builder.
        """
        try:
            # Use the response builder from common utilities
            return self.response_builder.build_response_from_openai(
                response_data=raw_response,
                model=options.get("model"),
            )
        except Exception as e:
            logger.error(f"Failed to convert OpenAI response: {str(e)}")
            raise LLMServiceException(f"Response conversion failed: {str(e)}")

    # === OpenAI format conversion helpers ===

    def _convert_tools_to_openai_format(
        self, tools: List[FunctionDefinition]
    ) -> List[Dict[str, Any]]:
        """
        Convert function definitions to OpenAI tools format.
        """
        openai_tools = []
        for func_def in tools:
            if hasattr(func_def, "name"):
                # Convert FunctionDefinition to OpenAI format
                tool = {
                    "type": "function",
                    "function": {
                        "name": func_def.name,
                        "description": func_def.description,
                        "parameters": func_def.parameters,
                    },
                }
                openai_tools.append(tool)
            elif isinstance(func_def, dict):
                # Already in OpenAI format or convert if needed
                if "type" not in func_def:
                    tool = {"type": "function", "function": func_def}
                    openai_tools.append(tool)
                else:
                    openai_tools.append(func_def)
        return openai_tools

    def _convert_tool_choice_to_openai_format(self, tool_choice: ToolChoice) -> Any:
        """
        Convert tool choice to OpenAI format.
        """
        if isinstance(tool_choice, str):
            return tool_choice
        elif hasattr(tool_choice, "value"):
            return tool_choice.value
        else:
            return tool_choice
