"""
Service resolver for Git operations.

This module provides centralized logic for resolving the appropriate
Git service adapter based on repository context.
"""

from typing import Optional, Type, Dict, Any
import logging

from .context import RepositoryContext, GitServiceType
from .adapters.base_adapter import BaseGitAdapter

logger = logging.getLogger(__name__)


class GitServiceResolver:
    """
    Resolves the appropriate Git service adapter based on repository context.

    This class acts as a factory that creates the correct adapter instance
    based on the service type specified in the repository context.
    """

    _adapters: Dict[GitServiceType, Type[BaseGitAdapter]] = {}

    @classmethod
    def register_adapter(
        cls, service_type: GitServiceType, adapter_class: Type[BaseGitAdapter]
    ) -> None:
        """
        Register a Git service adapter.

        Args:
            service_type: The Git service type this adapter handles
            adapter_class: The adapter class to register
        """
        cls._adapters[service_type] = adapter_class
        logger.debug(
            f"Registered adapter {adapter_class.__name__} for service {service_type.value}"
        )

    @classmethod
    def get_adapter(cls, repository_context: RepositoryContext) -> BaseGitAdapter:
        """
        Get the appropriate Git service adapter for the given repository context.

        Args:
            repository_context: Repository context containing service information

        Returns:
            Configured adapter instance for the specified service

        Raises:
            ValueError: If no adapter is registered for the service type
            Exception: If adapter initialization fails
        """
        service_type = repository_context.service_type

        if service_type not in cls._adapters:
            available_services = [s.value for s in cls._adapters.keys()]
            raise ValueError(
                f"No adapter registered for service type '{service_type.value}'. "
                f"Available services: {available_services}"
            )

        adapter_class = cls._adapters[service_type]

        try:
            # Create adapter instance with repository context
            adapter = adapter_class(repository_context)
            logger.debug(
                f"Created adapter {adapter_class.__name__} for {repository_context.full_name}"
            )
            return adapter

        except Exception as e:
            logger.error(
                f"Failed to create adapter {adapter_class.__name__} for "
                f"{repository_context.full_name}: {str(e)}"
            )
            raise

    @classmethod
    def list_supported_services(cls) -> Dict[str, str]:
        """
        List all supported Git services.

        Returns:
            Dictionary mapping service type values to adapter class names
        """
        return {
            service_type.value: adapter_class.__name__
            for service_type, adapter_class in cls._adapters.items()
        }

    @classmethod
    def is_service_supported(cls, service_type: GitServiceType) -> bool:
        """
        Check if a service type is supported.

        Args:
            service_type: The service type to check

        Returns:
            True if the service is supported, False otherwise
        """
        return service_type in cls._adapters

    @classmethod
    def validate_repository_context(cls, repository_context: RepositoryContext) -> bool:
        """
        Validate that the repository context can be handled by an available adapter.

        Args:
            repository_context: Repository context to validate

        Returns:
            True if the context can be handled, False otherwise
        """
        try:
            return cls.is_service_supported(repository_context.service_type)
        except Exception as e:
            logger.warning(f"Repository context validation failed: {str(e)}")
            return False


# Convenience function for direct adapter resolution
def resolve_git_adapter(repository_context: RepositoryContext) -> BaseGitAdapter:
    """
    Convenience function to resolve a Git adapter from repository context.

    Args:
        repository_context: Repository context containing service information

    Returns:
        Configured adapter instance for the specified service

    Raises:
        ValueError: If no adapter is registered for the service type
        Exception: If adapter initialization fails
    """
    return GitServiceResolver.get_adapter(repository_context)
