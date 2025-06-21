"""
LLM service factory.

This module provides a factory for creating LLM service instances.
"""

from typing import Dict, Type, Optional

from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.core.exceptions import ServiceNotFoundError


class LLMServiceFactory:
    """
    Factory for creating LLM service instances.

    This factory maintains a registry of available LLM services and provides
    methods to create instances of these services.
    """

    # Registry of available LLM services
    _services: Dict[str, Type[LLMServiceBase]] = {}

    @classmethod
    def register(cls, provider_name: str, service_class: Type[LLMServiceBase]) -> None:
        """
        Register an LLM service implementation.

        Args:
            provider_name: The name of the LLM provider
            service_class: The service class for the provider
        """
        cls._services[provider_name.lower()] = service_class

    @classmethod
    def create(cls, provider: str, **config) -> LLMServiceBase:
        """
        Create an LLM service instance.

        Args:
            provider: The name of the LLM provider
            **config: Configuration options for the service

        Returns:
            LLMServiceBase: An instance of the requested LLM service

        Raises:
            ServiceNotFoundError: If the requested provider is not registered
        """
        provider = provider.lower()
        if provider not in cls._services:
            available_providers = list(cls._services.keys())
            raise ServiceNotFoundError(
                f"LLM provider '{provider}' not found. Available providers: {available_providers}"
            )

        service_class = cls._services[provider]
        return service_class(**config)

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """
        Get a list of available LLM providers.

        Returns:
            list[str]: List of registered provider names
        """
        return list(cls._services.keys())
