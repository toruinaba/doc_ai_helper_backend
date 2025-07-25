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
    def create_with_mcp(
        cls, provider: str, enable_mcp: bool = True, **config
    ) -> LLMServiceBase:
        """
        Create an LLM service instance with FastMCP integration.

        Args:
            provider: The name of the LLM provider
            enable_mcp: Whether to enable FastMCP integration
            **config: Configuration options for the service

        Returns:
            LLMServiceBase: An instance of the requested LLM service with FastMCP integration

        Raises:
            ServiceNotFoundError: If the requested provider is not registered
        """
        service = cls.create(provider, **config)

        if enable_mcp:
            try:
                from doc_ai_helper_backend.services.mcp.server import mcp_server

                # Set FastMCP server directly on the service (no adapter layer)
                if hasattr(service, "set_mcp_server"):
                    service.set_mcp_server(mcp_server)

            except ImportError as e:
                # FastMCP not available, continue without it
                pass

        return service

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """
        Get a list of available LLM providers.

        Returns:
            list[str]: List of registered provider names
        """
        return list(cls._services.keys())


# Register default LLM services
def _register_default_services():
    """Register default LLM service implementations."""
    try:
        from doc_ai_helper_backend.services.llm.openai_service import OpenAIService

        LLMServiceFactory.register("openai", OpenAIService)
    except ImportError:
        # OpenAI not available
        pass

    try:
        from doc_ai_helper_backend.services.llm.mock_service import MockLLMService

        LLMServiceFactory.register("mock", MockLLMService)
    except ImportError:
        # Mock service not available
        pass


# Register services when module is imported
_register_default_services()
