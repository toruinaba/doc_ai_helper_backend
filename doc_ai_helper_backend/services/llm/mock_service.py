"""
Mock LLM service for development and testing.

This module provides a mock implementation of the LLM service interface.
"""

import json
import time
import os
import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator

from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    LLMUsage,
    ProviderCapabilities,
    MessageItem,
    MessageRole,
)
from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.services.llm.template_manager import PromptTemplateManager
from doc_ai_helper_backend.services.llm.utils import optimize_conversation_history


class MockLLMService(LLMServiceBase):
    """
    Mock implementation of the LLM service interface.

    This service returns predefined responses for testing and development.
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
        self.response_delay = response_delay
        self.default_model = default_model
        self.template_manager = PromptTemplateManager()

        # Predefined responses for different query patterns
        self.response_patterns = {
            "hello": "Hello! I'm a mock LLM assistant. How can I help you today?",
            "help": "I'm a mock LLM service used for testing. You can ask me anything, but I'll respond with predefined answers.",
            "error": "I'm simulating an error response for testing purposes.",
            "time": f"The current mock time is {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "version": "Mock LLM Service v1.0.0",
        }

    async def query(
        self,
        prompt: str,
        conversation_history: Optional[List[MessageItem]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        Send a query to the mock LLM.

        Args:
            prompt: The prompt to send
            conversation_history: Previous messages in the conversation
            options: Additional options for the query

        Returns:
            LLMResponse: A mock response
        """
        if options is None:
            options = {}

        # Simulate processing delay
        await self._simulate_delay()  # Determine which model to use
        model = options.get("model", self.default_model)

        # Generate a response based on the prompt and conversation history
        if conversation_history:
            content = self._generate_contextual_response(prompt, conversation_history)
        else:
            content = self._generate_response(prompt)  # Calculate mock token usage
        prompt_tokens = len(prompt) // 4
        completion_tokens = len(content) // 4

        # Create response
        response = LLMResponse(
            content=content,
            model=model,
            provider="mock",
            usage=LLMUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            raw_response={
                "id": f"mock-{int(time.time())}",
                "created": int(time.time()),
                "model": model,
                "content": content,
            },
        )

        # Optimize conversation history if provided
        if conversation_history:
            optimized_history, optimization_info = optimize_conversation_history(
                conversation_history, max_tokens=4000
            )
            response.optimized_conversation_history = optimized_history
            response.history_optimization_info = optimization_info
        else:
            # No conversation history provided
            response.optimized_conversation_history = []
            response.history_optimization_info = {
                "was_optimized": False,
                "reason": "No conversation history provided",
            }

        return response

    async def get_capabilities(self) -> ProviderCapabilities:
        """
        Get the capabilities of the mock LLM provider.

        Returns:
            ProviderCapabilities: Mock capabilities
        """
        return ProviderCapabilities(
            available_models=["mock-model", "mock-model-large", "mock-model-small"],
            max_tokens={
                "mock-model": 4096,
                "mock-model-large": 8192,
                "mock-model-small": 2048,
            },
            supports_streaming=True,
            supports_function_calling=True,
            supports_vision=False,
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
        except Exception as e:
            # In case of error, return a simple concatenation of variables
            return f"Template '{template_id}' with variables: {json.dumps(variables)}"

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
        # Simple estimation: ~4 characters per token
        return len(text) // 4

    async def _simulate_delay(self) -> None:
        """
        Simulate network and processing delay.
        """
        if self.response_delay > 0:
            await asyncio.sleep(self.response_delay)

    def _generate_response(self, prompt: str) -> str:
        """
        Generate a response based on the prompt.

        Args:
            prompt: The input prompt

        Returns:
            str: A mock response
        """
        # Check for pattern matches
        prompt_lower = prompt.lower()

        for pattern, response in self.response_patterns.items():
            if pattern in prompt_lower:
                return response

        # Default response for no pattern match
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

    def _generate_contextual_response(
        self, prompt: str, history: List[MessageItem]
    ) -> str:
        """
        会話履歴を考慮した応答を生成する。

        Args:
            prompt: 現在のプロンプト
            history: 会話履歴

        Returns:
            str: 生成された応答
        """
        # パターンに一致する応答があればそれを使用
        for pattern, response in self.response_patterns.items():
            if pattern.lower() in prompt.lower():
                return f"{response} (会話履歴を考慮しています)"

        # システムメッセージがあるかチェック
        system_messages = [msg for msg in history if msg.role == MessageRole.SYSTEM]
        has_system_message = len(system_messages) > 0

        # 前回の質問を参照する場合
        if "前の質問" in prompt.lower() or "previous question" in prompt.lower():
            for msg in reversed(history):
                if msg.role == MessageRole.USER and msg.content != prompt:
                    return f"前の質問は「{msg.content}」でした。"

        # 過去の回答を参照する場合
        if (
            "前の回答" in prompt.lower()
            or "previous answer" in prompt.lower()
            or "last response" in prompt.lower()
        ):
            for msg in reversed(history):
                if msg.role == MessageRole.ASSISTANT:
                    return f"前回の回答は「{msg.content}」でした。"

        # 会話の長さに基づく応答
        if len(history) > 2:
            base_response = f"会話の文脈を考慮した応答です。これまでに{len(history)}回のやり取りがありました。"
            if has_system_message:
                system_info = f" システム指示 [system] が設定されています: 「{system_messages[0].content[:30]}...」"
                return f"{base_response}{system_info}\n実際のプロンプト: {prompt}"
            return f"{base_response}\n実際のプロンプト: {prompt}"  # 会話履歴の要約
        conversation_summary = "\n".join(
            [f"[{msg.role.value}]: {msg.content[:30]}..." for msg in history[-3:]]
        )

        # デフォルトの応答
        return f"これはモック応答です。会話履歴に基づいて生成されました。\n\n最近の会話:\n{conversation_summary}\n\n現在の質問: {prompt}"

    async def stream_query(
        self,
        prompt: str,
        conversation_history: Optional[List[MessageItem]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a query to the mock LLM.

        Args:
            prompt: The prompt to send
            conversation_history: Previous messages in the conversation
            options: Additional options for the query

        Returns:
            AsyncGenerator[str, None]: An async generator that yields chunks of the response
        """
        if options is None:
            options = {}

        # Get the full response based on conversation history
        if conversation_history:
            full_response = self._generate_contextual_response(
                prompt, conversation_history
            )
        else:
            full_response = self._generate_response(prompt)

        # Split into chunks of approximately 10-20 characters
        chunks = []
        chunk_size = 15  # Average chunk size

        # Create chunks with natural word boundaries where possible
        start = 0
        while start < len(full_response):
            # Determine a variable chunk size around the average
            current_chunk_size = (
                chunk_size + (hash(full_response[start : start + 5]) % 10) - 5
            )

            # Make sure we don't go beyond the string length
            end = min(start + current_chunk_size, len(full_response))

            # Try to end at a space for more natural chunks
            if end < len(full_response) and not full_response[end].isspace():
                # Look for the nearest space backward
                space_pos = full_response.rfind(" ", start, end)
                if space_pos > start:
                    end = space_pos + 1

            chunks.append(full_response[start:end])
            start = end

        # Simulate streaming by yielding chunks with delays
        for chunk in chunks:
            # Simulate processing delay (shorter than full query to make streaming feel real)
            delay = min(0.3, self.response_delay / len(chunks))
            await asyncio.sleep(delay)

            yield chunk
