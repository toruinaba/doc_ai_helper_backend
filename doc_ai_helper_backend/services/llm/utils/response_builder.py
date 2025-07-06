"""
Response building utilities for LLM services.

This module provides utilities for building standardized LLMResponse objects
from different provider-specific response formats.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    LLMUsage,
    ToolCall,
    FunctionCall,
)

logger = logging.getLogger(__name__)


class LLMResponseBuilder:
    """
    Utility class for building standardized LLMResponse objects.

    This class provides methods to construct LLMResponse objects from various
    provider-specific response formats, ensuring consistency across all LLM services.
    """

    @staticmethod
    def build_usage_from_dict(usage_data: Dict[str, Any]) -> LLMUsage:
        """
        Build LLMUsage object from usage data dictionary.

        Args:
            usage_data: Dictionary containing token usage information

        Returns:
            LLMUsage: Standardized usage object
        """
        return LLMUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

    @staticmethod
    def build_usage_from_openai(usage_obj: Any) -> LLMUsage:
        """
        Build LLMUsage object from OpenAI usage object.

        Args:
            usage_obj: OpenAI usage object

        Returns:
            LLMUsage: Standardized usage object
        """
        if not usage_obj:
            return LLMUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

        return LLMUsage(
            prompt_tokens=getattr(usage_obj, "prompt_tokens", 0),
            completion_tokens=getattr(usage_obj, "completion_tokens", 0),
            total_tokens=getattr(usage_obj, "total_tokens", 0),
        )

    @staticmethod
    def build_base_response(
        content: str,
        model: str,
        provider: str,
        usage: LLMUsage,
        raw_response: Any,
        tool_calls: Optional[List[ToolCall]] = None,
        additional_fields: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        Build a standardized LLMResponse object.

        Args:
            content: The response content
            model: Model name used
            provider: Provider name (e.g., "openai", "mock")
            usage: Token usage information
            raw_response: Original provider response
            tool_calls: List of tool calls if any
            additional_fields: Additional fields to set on the response

        Returns:
            LLMResponse: Standardized response object
        """
        response = LLMResponse(
            content=content,
            model=model,
            provider=provider,
            usage=usage,
            raw_response=raw_response,
            tool_calls=tool_calls,
        )

        # Set additional fields if provided
        if additional_fields:
            for key, value in additional_fields.items():
                setattr(response, key, value)

        logger.debug(
            f"Built LLMResponse: provider={provider}, model={model}, content_length={len(content)}"
        )
        return response

    @staticmethod
    def build_from_openai_response(
        raw_response: Any, model: str, provider: str = "openai"
    ) -> LLMResponse:
        """
        Build LLMResponse from OpenAI API response.

        Args:
            raw_response: OpenAI API response object
            model: Model name to use in response
            provider: Provider name (defaults to "openai")

        Returns:
            LLMResponse: Standardized response object
        """
        try:
            # Extract content from the response
            message = raw_response.choices[0].message
            content = message.content or ""

            # Handle function/tool calls if present
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

            # Build usage information
            usage = LLMResponseBuilder.build_usage_from_openai(raw_response.usage)

            # Build and return response
            return LLMResponseBuilder.build_base_response(
                content=content,
                model=model,
                provider=provider,
                usage=usage,
                raw_response=raw_response.model_dump(),
                tool_calls=tool_calls if tool_calls else None,
            )

        except Exception as e:
            logger.error(f"Failed to build response from OpenAI: {str(e)}")
            raise ValueError(f"OpenAI response conversion failed: {str(e)}")

    @staticmethod
    def build_from_mock_response(
        raw_response: Dict[str, Any], default_model: str, provider: str = "mock"
    ) -> LLMResponse:
        """
        Build LLMResponse from Mock service response.

        Args:
            raw_response: Mock service response dictionary
            default_model: Default model name to use if not in response
            provider: Provider name (defaults to "mock")

        Returns:
            LLMResponse: Standardized response object
        """
        try:
            # Extract basic information
            content = raw_response.get("content", "")
            model = raw_response.get("model", default_model)

            # Build usage information
            usage_data = raw_response.get("usage", {})
            usage = LLMResponseBuilder.build_usage_from_dict(usage_data)

            # Mock-specific additional fields
            additional_fields = {
                "history_optimization_info": {
                    "was_optimized": False,
                    "reason": "Mock service does not optimize conversation history",
                    "original_length": 0,
                    "optimized_length": 0,
                },
                "optimized_conversation_history": [],
            }

            # Build and return response
            return LLMResponseBuilder.build_base_response(
                content=content,
                model=model,
                provider=provider,
                usage=usage,
                raw_response=raw_response,
                additional_fields=additional_fields,
            )

        except Exception as e:
            logger.error(f"Failed to build response from Mock: {str(e)}")
            raise ValueError(f"Mock response conversion failed: {str(e)}")

    @staticmethod
    def build_from_generic_response(
        content: str,
        model: str,
        provider: str,
        usage_data: Optional[Dict[str, Any]] = None,
        raw_response: Any = None,
        tool_calls: Optional[List[ToolCall]] = None,
    ) -> LLMResponse:
        """
        Build LLMResponse from generic response data.

        This is useful for other providers or custom implementations.

        Args:
            content: Response content
            model: Model name
            provider: Provider name
            usage_data: Token usage information
            raw_response: Original response object/dict
            tool_calls: List of tool calls if any

        Returns:
            LLMResponse: Standardized response object
        """
        # Build usage information
        usage = LLMResponseBuilder.build_usage_from_dict(usage_data or {})

        # Build and return response
        return LLMResponseBuilder.build_base_response(
            content=content,
            model=model,
            provider=provider,
            usage=usage,
            raw_response=raw_response or {},
            tool_calls=tool_calls,
        )
