"""
OpenAI response converter.

This module handles the conversion of OpenAI API responses to standardized LLMResponse objects.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletion

from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    LLMUsage,
    ToolCall,
    FunctionCall,
)

logger = logging.getLogger(__name__)


class OpenAIResponseConverter:
    """Converter class for transforming OpenAI API responses."""

    @staticmethod
    def convert_to_llm_response(
        openai_response: "ChatCompletion", model: str
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
        content = message.content or ""

        # Handle function/tool calls if present
        tool_calls = OpenAIResponseConverter._extract_tool_calls(message)

        # Create usage information
        usage = OpenAIResponseConverter._create_usage_info(openai_response)

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

    @staticmethod
    def _extract_tool_calls(message) -> list[ToolCall]:
        """
        Extract tool calls from OpenAI message.

        Args:
            message: OpenAI chat message

        Returns:
            list[ToolCall]: List of extracted tool calls
        """
        tool_calls = []

        if hasattr(message, "tool_calls") and message.tool_calls:
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

        return tool_calls

    @staticmethod
    def _create_usage_info(openai_response: "ChatCompletion") -> LLMUsage:
        """
        Create usage information from OpenAI response.

        Args:
            openai_response: OpenAI API response

        Returns:
            LLMUsage: Usage information
        """
        # Handle case where usage might be None
        if openai_response.usage:
            return LLMUsage(
                prompt_tokens=openai_response.usage.prompt_tokens,
                completion_tokens=openai_response.usage.completion_tokens,
                total_tokens=openai_response.usage.total_tokens,
            )
        else:
            # Create default usage if not provided
            logger.warning("OpenAI response missing usage information, using defaults")
            return LLMUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
