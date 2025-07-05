"""
OpenAI API client.

This module provides a focused client for making calls to the OpenAI API,
handling both synchronous and asynchronous operations with proper logging.
"""

import logging
from typing import Dict, Any, Optional, AsyncGenerator, TYPE_CHECKING

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletion

from openai import OpenAI, AsyncOpenAI

logger = logging.getLogger(__name__)


class OpenAIAPIClient:
    """Client class for making OpenAI API calls."""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
    ):
        """
        Initialize the OpenAI API client.

        Args:
            api_key: The OpenAI API key or proxy server API key
            base_url: Optional base URL for the API (e.g., LiteLLM proxy URL)
        """
        self.api_key = api_key
        self.base_url = base_url

        # Initialize OpenAI clients
        client_params = {"api_key": api_key}
        if base_url:
            client_params["base_url"] = base_url

        self.sync_client = OpenAI(**client_params)
        self.async_client = AsyncOpenAI(**client_params)

        logger.info(
            f"Initialized OpenAI API client"
            f"{' with custom base URL' if base_url else ''}"
        )

    async def call_api(self, options: Dict[str, Any]) -> "ChatCompletion":
        """
        Call the OpenAI API (or LiteLLM proxy) with the prepared options.

        Args:
            options: Prepared options for the API call

        Returns:
            ChatCompletion: The response from the OpenAI API
        """
        # Extract messages and model from options
        messages = options.pop("messages")
        model = options.pop("model")

        # Log API call details
        self._log_api_call_details(model, messages, options)

        # Make the API call
        response = await self.async_client.chat.completions.create(
            model=model, messages=messages, **options
        )

        # Log response details
        self._log_api_response_details(response)

        return response

    async def stream_api(self, options: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Stream a query to the OpenAI API.

        Args:
            options: Prepared options for the API call

        Yields:
            str: Chunks of the response content
        """
        # Extract messages and model from options
        messages = options.pop("messages")
        model = options.pop("model")

        # Ensure streaming is enabled
        options["stream"] = True

        # Log API call details
        self._log_api_call_details(model, messages, options)

        try:
            # Make the streaming API call
            stream = await self.async_client.chat.completions.create(
                model=model, messages=messages, **options
            )

            # Yield chunks as they arrive
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Error in streaming API call: {str(e)}")
            raise

    def _log_api_call_details(
        self, model: str, messages: list, options: Dict[str, Any]
    ) -> None:
        """
        Log details about the API call for debugging.

        Args:
            model: The model being used
            messages: The messages being sent
            options: Additional options
        """
        logger.info(f"Calling API with model: {model}")
        logger.info(
            f"Base URL: {self.async_client.base_url if hasattr(self.async_client, 'base_url') else 'default'}"
        )
        logger.info(f"Messages count: {len(messages)}")
        logger.info(f"Has tools: {'tools' in options}")

        if "tools" in options:
            logger.info(f"Tools count: {len(options['tools'])}")

        # Log last few messages for debugging
        for i, msg in enumerate(messages[-3:]):  # Last 3 messages
            role = msg.get("role", "unknown")
            content_preview = (
                str(msg.get("content", ""))[:100] if msg.get("content") else "None"
            )
            logger.info(f"Message {len(messages)-3+i}: {role} - {content_preview}...")

            if "tool_calls" in msg:
                logger.info(f"  Has tool_calls: {len(msg['tool_calls'])}")
            if role == "tool":
                logger.info(f"  Tool call ID: {msg.get('tool_call_id', 'missing')}")

    def _log_api_response_details(self, response: "ChatCompletion") -> None:
        """
        Log details about the API response for debugging.

        Args:
            response: The OpenAI API response
        """
        logger.info(f"API Response model: {response.model}")
        logger.info(f"API Response choices count: {len(response.choices)}")

        if response.choices:
            choice = response.choices[0]
            logger.info(f"First choice finish_reason: {choice.finish_reason}")
            logger.info(
                f"First choice content length: {len(choice.message.content) if choice.message.content else 0}"
            )
            logger.info(
                f"First choice content preview: {choice.message.content[:100] if choice.message.content else 'None'}..."
            )
            logger.info(
                f"First choice has tool_calls: {bool(choice.message.tool_calls)}"
            )

            if choice.message.tool_calls:
                logger.info(f"Tool calls count: {len(choice.message.tool_calls)}")
                for i, tc in enumerate(choice.message.tool_calls):
                    logger.info(
                        f"Tool call {i}: {tc.function.name} with args: {tc.function.arguments[:100]}..."
                    )
