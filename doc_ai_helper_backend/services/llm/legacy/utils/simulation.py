"""
Simulation utilities for testing and development.

This module provides utilities for simulating delays, errors, and other
testing scenarios across different LLM service implementations.
"""

import asyncio
from typing import Optional
from doc_ai_helper_backend.core.exceptions import LLMServiceException


class SimulationUtils:
    """Utilities for simulating various conditions in LLM services."""

    @staticmethod
    async def simulate_delay(delay: float) -> None:
        """
        Simulate network and processing delay.

        Args:
            delay: Delay time in seconds. If <= 0, no delay is applied.
        """
        if delay > 0:
            await asyncio.sleep(delay)

    @staticmethod
    def should_simulate_error(
        prompt: str, error_keywords: Optional[list] = None
    ) -> bool:
        """
        Check if an error should be simulated based on prompt content.

        Args:
            prompt: The user prompt to check
            error_keywords: List of keywords that trigger error simulation.
                          If None, uses default keywords.

        Returns:
            True if an error should be simulated, False otherwise
        """
        if error_keywords is None:
            error_keywords = ["simulate_error", "force_error", "test_error"]

        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in error_keywords)

    @staticmethod
    def raise_simulated_error(
        message: str = "Simulated error for testing purposes",
    ) -> None:
        """
        Raise a simulated LLM service error.

        Args:
            message: The error message to include in the exception

        Raises:
            LLMServiceException: Always raises this exception
        """
        raise LLMServiceException(message)

    @staticmethod
    async def check_and_raise_error_if_needed(
        prompt: str, error_keywords: Optional[list] = None
    ) -> None:
        """
        Check prompt for error simulation keywords and raise error if needed.

        Args:
            prompt: The user prompt to check
            error_keywords: List of keywords that trigger error simulation.
                          If None, uses default keywords.

        Raises:
            LLMServiceException: If error simulation is triggered
        """
        if SimulationUtils.should_simulate_error(prompt, error_keywords):
            SimulationUtils.raise_simulated_error()
