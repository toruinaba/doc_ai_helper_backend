"""
OpenAI LLM service.

This module provides an implementation of the LLM service using OpenAI's API.
It can be used with OpenAI directly or with a LiteLLM proxy server.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple, AsyncGenerator

import tiktoken
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion

from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.services.llm.template_manager import PromptTemplateManager
from doc_ai_helper_backend.services.llm.cache_service import LLMCacheService
from doc_ai_helper_backend.services.llm.utils import (
    format_conversation_for_provider,
    optimize_conversation_history,
)
from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    LLMUsage,
    ProviderCapabilities,
    MessageItem,
    FunctionDefinition,
    FunctionCall,
    ToolChoice,
    ToolCall,
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

        # Initialize template manager
        self.template_manager = PromptTemplateManager()

        # Initialize cache service
        self.cache_service = LLMCacheService()

        # Initialize OpenAI clients
        client_params = {"api_key": api_key}
        if base_url:
            client_params["base_url"] = base_url

        self.sync_client = OpenAI(**client_params)
        self.async_client = AsyncOpenAI(**client_params)

        # Initialize MCP integration
        self._mcp_adapter = None
        self._function_call_manager = None

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

    async def query(
        self,
        prompt: str,
        conversation_history: Optional[List["MessageItem"]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        Send a query to the LLM.

        Args:
            prompt: The prompt to send to the LLM
            conversation_history: Previous messages in the conversation
            options: Additional options for the query (model, temperature, etc.)

        Returns:
            LLMResponse: The response from the LLM
        """
        options = options or {}

        # Prepare query options
        query_options = self._prepare_options(prompt, options, conversation_history)
        model = query_options.get("model", self.default_model)

        # Check if cache should be bypassed
        disable_cache = query_options.pop(
            "disable_cache", False
        )  # Check cache before making API call (if not disabled)
        if not disable_cache:
            cache_key = self.cache_service.generate_key(prompt, query_options)
            cached_response = self.cache_service.get(cache_key)
            if cached_response:
                logger.debug(f"Cache hit for prompt with key {cache_key[:8]}")
                return cached_response
        else:
            logger.debug("Cache disabled for this request")
            cache_key = None

        try:
            # Call OpenAI API
            logger.debug(f"Sending query to OpenAI with model {model}")
            response = await self._call_openai_api(query_options)

            # Convert OpenAI response to LLMResponse
            llm_response = self._convert_to_llm_response(
                response, model
            )  # Optimize conversation history if provided
            if conversation_history:
                optimized_history, optimization_info = optimize_conversation_history(
                    conversation_history, max_tokens=4000
                )
                llm_response.optimized_conversation_history = optimized_history
                llm_response.history_optimization_info = optimization_info
            else:
                # No conversation history provided
                llm_response.optimized_conversation_history = []
                llm_response.history_optimization_info = {
                    "was_optimized": False,
                    "reason": "No conversation history provided",
                }

            # Cache the response (if caching is not disabled)
            if not disable_cache and cache_key:
                self.cache_service.set(cache_key, llm_response)

            return llm_response

        except Exception as e:
            logger.error(f"Error querying OpenAI: {str(e)}")
            raise LLMServiceException(message=f"Error querying OpenAI: {str(e)}")

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
        return self.template_manager.get_template_ids()

    async def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text.

        Args:
            text: The text to estimate tokens for

        Returns:
            int: Estimated token count
        """
        return len(self._token_encoder.encode(text))

    def _prepare_options(
        self,
        prompt: str,
        options: Dict[str, Any],
        conversation_history: Optional[List["MessageItem"]] = None,
    ) -> Dict[str, Any]:
        """
        Prepare options for the OpenAI API call.

        Args:
            prompt: The prompt text
            options: User-provided options
            conversation_history: Previous messages in the conversation

        Returns:
            Dict[str, Any]: Prepared options for the API call
        """
        # Start with default options
        prepared_options = {
            "model": self.default_model,
            "temperature": 0.7,
            "max_tokens": 1000,
        }

        # Handle messages - use provided messages if available, otherwise create from conversation history and prompt
        if "messages" in options:
            prepared_options["messages"] = options["messages"]
        else:
            # If conversation history exists, format it for OpenAI
            if conversation_history:
                messages = format_conversation_for_provider(
                    conversation_history, provider="openai"
                )
                # Add current prompt as the latest user message
                messages.append({"role": "user", "content": prompt})
                prepared_options["messages"] = messages
            else:
                # No conversation history, just use the prompt
                prepared_options["messages"] = [
                    {"role": "user", "content": prompt}
                ]  # If a model was specified, use it
        if "model" in options:
            prepared_options["model"] = options["model"]

        # Log the model being used
        logger.info(f"Using OpenAI model: {prepared_options['model']}")
        if "context_documents" in options and options["context_documents"]:
            # In a real implementation, you would process these documents
            # through the MCP adapter and add them to the messages
            pass

        # Handle function calling - include tools if provided
        if "functions" in options and options["functions"]:
            # Convert function definitions to OpenAI tools format
            tools = []
            for func_def in options["functions"]:
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
                    tools.append(tool)
                elif isinstance(func_def, dict):
                    # Already in correct format
                    tools.append(func_def)

            if tools:
                prepared_options["tools"] = tools
                # Set tool_choice if specified
                if "tool_choice" in options:
                    prepared_options["tool_choice"] = options[
                        "tool_choice"
                    ]  # Override default options with user-provided options
        for key, value in options.items():
            if key not in [
                "model",
                "messages",
                "context_documents",
                "enable_function_calling",
                "available_functions",
            ]:
                prepared_options[key] = value

        # Handle custom function calling parameters
        if options.get("enable_function_calling") and options.get(
            "available_functions"
        ):
            # Convert available_functions to OpenAI tools format
            tools = []
            for func_name in options["available_functions"]:
                # Create a basic tool definition
                # In a real implementation, you would get the actual function schema
                tool = {
                    "type": "function",
                    "function": {
                        "name": func_name,
                        "description": f"Call the {func_name} function",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    },
                }
                tools.append(tool)

            if tools:
                prepared_options["tools"] = tools

        return prepared_options

    async def _call_openai_api(self, options: Dict[str, Any]) -> ChatCompletion:
        """
        Call the OpenAI API with the prepared options.

        Args:
            options: Prepared options for the API call

        Returns:
            ChatCompletion: The response from the OpenAI API
        """
        # Extract messages and model from options
        messages = options.pop("messages")
        model = options.pop("model")

        # Make the API call
        response = await self.async_client.chat.completions.create(
            model=model, messages=messages, **options
        )

        return response

    def _convert_to_llm_response(
        self, openai_response: ChatCompletion, model: str
    ) -> LLMResponse:
        """
        Convert an OpenAI API response to an LLMResponse.

        Args:
            openai_response: The response from the OpenAI API
            model: The model used for the query

        Returns:
            LLMResponse: The standardized LLM response
        """
        # Extract content from the response
        message = openai_response.choices[0].message
        content = message.content or ""  # Handle function/tool calls if present
        tool_calls = []
        if hasattr(message, "tool_calls") and message.tool_calls:
            from doc_ai_helper_backend.models.llm import ToolCall, FunctionCall

            for tool_call in message.tool_calls:
                if tool_call.type == "function":
                    function_call = FunctionCall(
                        name=tool_call.function.name,
                        arguments=tool_call.function.arguments,
                    )
                    tool_call_obj = ToolCall(
                        id=tool_call.id, type="function", function=function_call
                    )
                    tool_calls.append(tool_call_obj)

        # Create usage information (handle case where usage might be None)
        usage = None
        if openai_response.usage:
            usage = LLMUsage(
                prompt_tokens=openai_response.usage.prompt_tokens,
                completion_tokens=openai_response.usage.completion_tokens,
                total_tokens=openai_response.usage.total_tokens,
            )
        else:
            # Create default usage if not provided
            usage = LLMUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

        # Create and return the response
        response = LLMResponse(
            content=content,
            model=model,
            provider="openai",
            usage=usage,
            raw_response=openai_response.model_dump(),
            tool_calls=tool_calls if tool_calls else None,
        )

        return response

    async def stream_query(
        self,
        prompt: str,
        conversation_history: Optional[List["MessageItem"]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a query to the LLM.

        Args:
            prompt: The prompt to send to the LLM
            conversation_history: Previous messages in the conversation
            options: Additional options for the query (model, temperature, etc.)

        Returns:
            AsyncGenerator[str, None]: An async generator that yields chunks of the response
        """
        options = options or {}
        query_options = self._prepare_options(prompt, options, conversation_history)
        model = query_options.get("model", self.default_model)

        try:
            # OpenAI APIにリクエスト
            messages = query_options.pop("messages")
            # modelキーとstreamキーをquery_optionsから削除して重複を防ぐ
            query_options.pop("model", None)
            query_options.pop("stream", None)

            # ストリーミングレスポンスを取得
            stream = await self.async_client.chat.completions.create(
                model=model, messages=messages, stream=True, **query_options
            )

            # チャンクを順次生成
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

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
        if mcp_adapter:
            self._function_call_manager = mcp_adapter.get_function_registry()
            logger.info("MCP adapter configured for OpenAI service")

    async def query_with_tools(
        self,
        prompt: str,
        tools: List["FunctionDefinition"],
        conversation_history: Optional[List["MessageItem"]] = None,
        tool_choice: Optional["ToolChoice"] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        Send a query to the LLM with function calling tools.

        Args:
            prompt: The prompt to send to the LLM
            tools: List of available function definitions
            conversation_history: Previous messages in the conversation for context
            tool_choice: Strategy for tool selection
            options: Additional options for the query

        Returns:
            LLMResponse: The response from the LLM, potentially including tool calls
        """
        # Prepare options with function definitions
        query_options = options or {}
        query_options["functions"] = tools

        if tool_choice:
            query_options["tool_choice"] = tool_choice

        return await self.query(prompt, conversation_history, query_options)

    async def get_available_functions(self) -> List["FunctionDefinition"]:
        """
        Get the list of available functions for this LLM service.

        Returns:
            List[FunctionDefinition]: List of available function definitions
        """
        all_functions = []

        # Add MCP adapter functions (if available)
        if self._mcp_adapter:
            all_functions.extend(self._mcp_adapter.get_available_functions())
        # Add GitHub functions
        from doc_ai_helper_backend.services.llm.github_functions import (
            get_github_function_definitions,
        )

        all_functions.extend(get_github_function_definitions())

        # Add utility functions
        from doc_ai_helper_backend.services.llm.utility_functions import (
            get_utility_functions,
        )

        all_functions.extend(get_utility_functions())

        return all_functions

    async def execute_function_call(
        self,
        function_call: "FunctionCall",
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
        if self._mcp_adapter:
            return await self._mcp_adapter.execute_function_call(function_call)
        else:
            return {
                "success": False,
                "error": "MCP adapter not configured",
                "result": None,
            }
