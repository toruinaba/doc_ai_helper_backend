"""
Test utility methods for the Mock LLM service.

This module contains utility methods specifically designed for testing purposes
and backward compatibility with existing test suites.
"""

from typing import List
from doc_ai_helper_backend.models.llm import MessageItem
from .response_generator import MockResponseGenerator


class MockTestUtilities:
    """Test utility methods for MockLLMService."""

    @staticmethod
    def should_call_github_function(prompt: str) -> bool:
        """
        Determine if the prompt suggests a GitHub/Git operation should be performed.

        This method is used by tests to verify function calling logic.
        Delegates to the response generator for consistency.
        """
        return MockResponseGenerator.should_call_github_function(prompt)

    @staticmethod
    def should_call_utility_function(prompt: str) -> bool:
        """
        Determine if the prompt suggests a utility operation should be performed.

        This method is used by tests to verify function calling logic.
        Delegates to the response generator for consistency.
        """
        return MockResponseGenerator.should_call_utility_function(prompt)

    @staticmethod
    def should_call_analysis_function(prompt: str) -> bool:
        """
        Determine if the prompt suggests an analysis operation should be performed.

        This method is used by tests to verify function calling logic.
        Delegates to the response generator for consistency.
        """
        return MockResponseGenerator.should_call_analysis_function(prompt)

    @staticmethod
    def generate_contextual_response(
        prompt: str,
        history: List[MessageItem],
        system_prompt: str = None,
    ) -> str:
        """
        Generate a response considering conversation history.

        This method is used by tests to verify conversation handling.
        Delegates to the response generator for consistency.
        """
        return MockResponseGenerator.generate_contextual_response(
            prompt, history, system_prompt
        )
