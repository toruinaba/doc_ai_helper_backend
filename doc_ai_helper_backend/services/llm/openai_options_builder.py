"""
OpenAI options builder.

This module handles the preparation of options for OpenAI API calls,
including message construction, function definitions, and parameter validation.
"""

import logging
from typing import Dict, Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from doc_ai_helper_backend.models.llm import MessageItem

from doc_ai_helper_backend.services.llm.utils import format_conversation_for_provider

logger = logging.getLogger(__name__)


class OpenAIOptionsBuilder:
    """Builder class for preparing OpenAI API call options."""

    def __init__(self, default_model: str = "gpt-3.5-turbo"):
        """
        Initialize the options builder.

        Args:
            default_model: Default model to use for API calls
        """
        self.default_model = default_model

    def prepare_options(
        self,
        prompt: str,
        options: Dict[str, Any],
        conversation_history: Optional[List["MessageItem"]] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Prepare options for the OpenAI API call.

        Args:
            prompt: The prompt text
            options: User-provided options
            conversation_history: Previous messages in the conversation
            system_prompt: System prompt to include as first message

        Returns:
            Dict[str, Any]: Prepared options for the API call
        """
        # Start with default options
        prepared_options = {
            "model": self.default_model,
            "temperature": 0.7,
            "max_tokens": 1000,
        }

        # Handle messages
        prepared_options["messages"] = self._build_messages(
            prompt, options, conversation_history, system_prompt
        )

        # Handle model selection
        if "model" in options:
            prepared_options["model"] = options["model"]

        logger.info(f"Using OpenAI model: {prepared_options['model']}")

        # Handle function calling
        self._handle_function_calling(options, prepared_options)

        # Override default options with user-provided options
        self._apply_user_options(options, prepared_options)

        return prepared_options

    def _build_messages(
        self,
        prompt: str,
        options: Dict[str, Any],
        conversation_history: Optional[List["MessageItem"]] = None,
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Build the messages array for OpenAI API.

        Args:
            prompt: The current prompt
            options: User-provided options
            conversation_history: Previous conversation messages
            system_prompt: System prompt to include

        Returns:
            List[Dict[str, Any]]: Messages formatted for OpenAI API
        """
        # Use provided messages if available
        if "messages" in options:
            logger.info(
                f"Using provided messages ({len(options['messages'])} messages)"
            )
            return options["messages"]

        messages = []

        # Add system prompt as first message if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            logger.info("Added system prompt to messages")

        # Add conversation history
        if conversation_history:
            history_messages = format_conversation_for_provider(
                conversation_history, provider="openai"
            )
            messages.extend(history_messages)

        # Add current prompt as the latest user message (only if prompt is not empty)
        if prompt.strip():
            messages.append({"role": "user", "content": prompt})

        return messages

    def _handle_function_calling(
        self, options: Dict[str, Any], prepared_options: Dict[str, Any]
    ) -> None:
        """
        Handle function calling options.

        Args:
            options: User-provided options
            prepared_options: Options being prepared for API call
        """
        # Support both legacy 'functions' parameter and new 'tools' parameter
        if "functions" in options and options["functions"]:
            tools = self._convert_functions_to_tools(options["functions"])
            if tools:
                prepared_options["tools"] = tools

        elif "tools" in options and options["tools"]:
            tools = self._convert_tools_format(options["tools"])
            if tools:
                prepared_options["tools"] = tools
                # Set tool_choice if specified
                if "tool_choice" in options:
                    prepared_options["tool_choice"] = options["tool_choice"]

        # Handle custom function calling parameters
        elif options.get("enable_function_calling") and options.get(
            "available_functions"
        ):
            tools = self._create_basic_tools(options["available_functions"])
            if tools:
                prepared_options["tools"] = tools

    def _convert_functions_to_tools(self, functions: List[Any]) -> List[Dict[str, Any]]:
        """
        Convert legacy functions format to tools format.

        Args:
            functions: List of function definitions

        Returns:
            List[Dict[str, Any]]: Tools in OpenAI format
        """
        tools = []
        for func_def in functions:
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
                # Convert from function definition format
                tool = {"type": "function", "function": func_def}
                tools.append(tool)
        return tools

    def _convert_tools_format(self, tools_input: List[Any]) -> List[Dict[str, Any]]:
        """
        Convert function definitions to OpenAI tools format.

        Args:
            tools_input: List of tool definitions

        Returns:
            List[Dict[str, Any]]: Tools in OpenAI format
        """
        tools = []
        for func_def in tools_input:
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
                # Already in correct format or convert if needed
                if "type" not in func_def:
                    # Convert from function definition format
                    tool = {"type": "function", "function": func_def}
                    tools.append(tool)
                else:
                    tools.append(func_def)
        return tools

    def _create_basic_tools(
        self, available_functions: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Create basic tool definitions from function names.

        Args:
            available_functions: List of function names

        Returns:
            List[Dict[str, Any]]: Basic tool definitions
        """
        tools = []
        for func_name in available_functions:
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
        return tools

    def _apply_user_options(
        self, options: Dict[str, Any], prepared_options: Dict[str, Any]
    ) -> None:
        """
        Apply user-provided options to prepared options.

        Args:
            options: User-provided options
            prepared_options: Options being prepared for API call
        """
        excluded_keys = {
            "model",
            "messages",
            "context_documents",
            "enable_function_calling",
            "available_functions",
            "functions",
            "tools",
            "tool_choice",
        }

        for key, value in options.items():
            if key not in excluded_keys:
                prepared_options[key] = value
