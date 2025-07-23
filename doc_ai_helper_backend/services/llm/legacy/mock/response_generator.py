"""
Response generation logic for the Mock LLM service.

This module contains all the logic for generating different types of mock responses
based on prompts, context, and conversation history.
"""

import time
from typing import Dict, Any, Optional, List
from doc_ai_helper_backend.models.llm import MessageItem, MessageRole
from .constants import (
    RESPONSE_PATTERNS,
    PREVIOUS_QUESTION_KEYWORDS,
    PREVIOUS_ANSWER_KEYWORDS,
    CONVERSATION_CONTINUATION_KEYWORDS,
    ERROR_KEYWORDS,
    GITHUB_KEYWORDS,
    UTILITY_KEYWORDS,
    ANALYSIS_KEYWORDS,
    CHARACTERS_PER_TOKEN,
)


class MockResponseGenerator:
    """Generates mock responses for various types of prompts and contexts."""

    @staticmethod
    def check_for_error_simulation(prompt: str) -> bool:
        """Check if the prompt should trigger an error simulation."""
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in ERROR_KEYWORDS)

    @staticmethod
    def should_call_github_function(prompt: str) -> bool:
        """
        Determine if the prompt suggests a GitHub/Git operation should be performed.

        This method is used by tests to verify function calling logic.
        """
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in GITHUB_KEYWORDS)

    @staticmethod
    def should_call_utility_function(prompt: str) -> bool:
        """
        Determine if the prompt suggests a utility operation should be performed.

        This method is used by tests to verify function calling logic.
        """
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in UTILITY_KEYWORDS)

    @staticmethod
    def should_call_analysis_function(prompt: str) -> bool:
        """
        Determine if the prompt suggests an analysis operation should be performed.

        This method is used by tests to verify function calling logic.
        """
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in ANALYSIS_KEYWORDS)

    @staticmethod
    def generate_simple_response(
        prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generate a simple mock response based on prompt patterns."""
        prompt_lower = prompt.lower()

        # Check for pattern matches first
        for pattern, response in RESPONSE_PATTERNS.items():
            if pattern in prompt_lower:
                return response

        # Handle conversation history references
        if any(keyword in prompt for keyword in PREVIOUS_QUESTION_KEYWORDS):
            return "What is Python?"  # This matches test expectations

        # Handle previous answer references
        if any(keyword in prompt for keyword in PREVIOUS_ANSWER_KEYWORDS):
            return "Python is a programming language."

        # Handle conversation continuation
        if any(
            keyword in prompt_lower for keyword in CONVERSATION_CONTINUATION_KEYWORDS
        ):
            if system_prompt:
                return "I understand you want to continue our conversation. As your assistant, I'm ready to help with any questions you may have."
            else:
                return "Let's continue our conversation. How can I assist you further?"

        # Check system prompt context
        if system_prompt:
            if "microsoft/vscode" in system_prompt:
                return f"I understand you're asking about Visual Studio Code. {prompt}"
            elif "github.com" in system_prompt or "repository" in system_prompt.lower():
                return (
                    f"I received your question about this repository context. {prompt}"
                )

        # Default responses based on prompt characteristics
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

    @staticmethod
    def generate_contextual_response(
        prompt: str,
        history: List[MessageItem],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate a response considering conversation history.

        This method is used by tests to verify conversation handling.
        """
        # Handle conversation continuation with system context
        if (
            any(
                keyword in prompt.lower()
                for keyword in CONVERSATION_CONTINUATION_KEYWORDS
            )
            and system_prompt
        ):
            return "I understand you want to continue our conversation. As your assistant, I'm ready to help with any questions you may have."

        # If system prompt is provided, include relevant information in response
        if system_prompt:
            if "microsoft/vscode" in system_prompt:
                return f"Based on our conversation history and the Visual Studio Code context, I understand: {prompt}"
            elif "test/minimal" in system_prompt:
                return f"Considering our previous exchanges about the test/minimal repository: {prompt}"
            elif "github.com" in system_prompt or "repository" in system_prompt.lower():
                return f"Taking into account the repository context and our conversation: {prompt}"

        # Check for pattern matches in response patterns
        for pattern, response in RESPONSE_PATTERNS.items():
            if pattern.lower() in prompt.lower():
                return f"{response} (会話履歴を考慮しています)"

        # Handle empty or invalid history
        if not history or not isinstance(history, list):
            simple_response = MockResponseGenerator.generate_simple_response(
                prompt, system_prompt
            )
            if prompt in simple_response:
                return simple_response
            else:
                return f"Contextual response for: {prompt}. " + simple_response

        # Filter valid MessageItems only
        valid_history = [
            msg for msg in history if hasattr(msg, "role") and hasattr(msg, "content")
        ]

        # Check for system messages
        system_messages = [
            msg for msg in valid_history if msg.role == MessageRole.SYSTEM
        ]
        has_system_message = len(system_messages) > 0

        # Handle references to previous questions
        if any(
            keyword.lower() in prompt.lower() for keyword in PREVIOUS_QUESTION_KEYWORDS
        ):
            for msg in reversed(valid_history):
                if msg.role == MessageRole.USER and msg.content != prompt:
                    return f"前の質問は「{msg.content}」でした。"

        # Handle references to previous answers
        if any(
            keyword.lower() in prompt.lower() for keyword in PREVIOUS_ANSWER_KEYWORDS
        ):
            for msg in reversed(valid_history):
                if msg.role == MessageRole.ASSISTANT:
                    return f"前回の回答は「{msg.content}」でした。"

        # Response based on conversation length
        if len(valid_history) > 2:
            base_response = f"会話の文脈を考慮した応答です。これまでに{len(valid_history)}回のやり取りがありました。"
            if has_system_message:
                system_info = f" システム指示 [system] が設定されています: 「{system_messages[0].content[:30]}...」"
                return f"{base_response}{system_info}\n実際のプロンプト: {prompt}"
            return f"{base_response}\n実際のプロンプト: {prompt}"

        # Generate conversation summary
        conversation_summary = "\n".join(
            [f"[{msg.role.value}]: {msg.content[:30]}..." for msg in history[-3:]]
        )

        # Default contextual response
        return f"これはモック応答です。会話履歴に基づいて生成されました。\n\n最近の会話:\n{conversation_summary}\n\n現在の質問: {prompt}"

    @staticmethod
    def generate_provider_response(
        prompt: str,
        system_prompt: Optional[str] = None,
        has_system_in_history: bool = False,
        default_model: str = "mock-model",
    ) -> Dict[str, Any]:
        """Generate a mock provider API response."""
        # Generate content considering system context
        if (has_system_in_history or system_prompt) and any(
            keyword in prompt.lower() for keyword in CONVERSATION_CONTINUATION_KEYWORDS
        ):
            content = "I understand you want to continue our conversation. As your assistant, I'm ready to help with any questions you may have."
        else:
            content = MockResponseGenerator.generate_simple_response(
                prompt, system_prompt
            )

        return {
            "content": content,
            "model": default_model,
            "usage": {
                "prompt_tokens": len(prompt) // CHARACTERS_PER_TOKEN,
                "completion_tokens": len(content) // CHARACTERS_PER_TOKEN,
                "total_tokens": (len(prompt) // CHARACTERS_PER_TOKEN)
                + (len(content) // CHARACTERS_PER_TOKEN),
            },
            "id": f"mock-{int(time.time())}",
            "created": int(time.time()),
        }

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate the number of tokens in a text using mock estimation."""
        return len(text) // CHARACTERS_PER_TOKEN
