"""
Base LLM service.

This module provides the base abstract class for LLM services.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncGenerator

from doc_ai_helper_backend.models.llm import LLMResponse, ProviderCapabilities


class LLMServiceBase(ABC):
    """
    Base class for LLM services.

    This abstract class defines the interface that all LLM service implementations
    must follow. It provides methods for querying LLMs, retrieving capabilities,
    and formatting prompts.
    """

    @abstractmethod
    async def query(
        self, prompt: str, options: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """
        Send a query to the LLM.

        Args:
            prompt: The prompt to send to the LLM
            options: Additional options for the query (model, temperature, etc.)

        Returns:
            LLMResponse: The response from the LLM
        """
        pass

    @abstractmethod
    async def get_capabilities(self) -> ProviderCapabilities:
        """
        Get the capabilities of the LLM provider.        Returns:
            ProviderCapabilities: The capabilities of the provider
        """
        pass

    @abstractmethod
    async def format_prompt(self, template_id: str, variables: Dict[str, Any]) -> str:
        """
        Format a prompt template with variables.

        Args:
            template_id: The ID of the template to use
            variables: The variables to substitute in the template

        Returns:
            str: The formatted prompt
        """
        pass

    @abstractmethod
    async def get_available_templates(self) -> List[str]:
        """
        Get a list of available prompt template IDs.

        Returns:
            List[str]: List of template IDs
        """
        pass

    @abstractmethod
    async def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text.

        Args:
            text: The text to estimate tokens for        Returns:
            int: Estimated token count
        """
        pass

    @abstractmethod
    async def stream_query(
        self, prompt: str, options: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream a query to the LLM.

        Args:
            prompt: The prompt to send to the LLM
            options: Additional options for the query (model, temperature, etc.)

        Returns:
            AsyncGenerator[str, None]: An async generator that yields chunks of the response
        """
        pass
