"""
Factory for creating MCP Git tools based on service configuration.

This module provides a factory pattern for creating appropriate Git tools
adapters based on the Git service type and configuration.
"""

import os
import logging
from typing import Dict, Any, Optional, Type, Union, List

from .base import MCPGitToolsBase
from .github_adapter import MCPGitHubAdapter
from .forgejo_adapter import MCPForgejoAdapter

logger = logging.getLogger(__name__)


class MCPGitToolsFactory:
    """Factory for creating MCP Git tools adapters."""

    # Registry of available Git tools adapters
    _adapters: Dict[str, Type[MCPGitToolsBase]] = {
        "github": MCPGitHubAdapter,
        "forgejo": MCPForgejoAdapter,
    }

    @classmethod
    def create(
        cls, service_type: str, config: Optional[Dict[str, Any]] = None, **kwargs
    ) -> MCPGitToolsBase:
        """
        Create a Git tools adapter based on service type and configuration.

        Args:
            service_type: Type of Git service ('github', 'forgejo', etc.)
            config: Service configuration dictionary
            **kwargs: Additional configuration parameters

        Returns:
            MCPGitToolsBase: Configured Git tools adapter

        Raises:
            ValueError: If service type is not supported
            KeyError: If required configuration is missing
        """
        if service_type not in cls._adapters:
            available_services = ", ".join(cls._adapters.keys())
            raise ValueError(
                f"Unsupported Git service type: {service_type}. "
                f"Available services: {available_services}"
            )

        adapter_class = cls._adapters[service_type]

        # Merge config and kwargs
        merged_config = {}
        if config:
            merged_config.update(config)
        merged_config.update(kwargs)

        # Create adapter with service-specific configuration
        if service_type == "github":
            return cls._create_github_adapter(merged_config)
        elif service_type == "forgejo":
            return cls._create_forgejo_adapter(merged_config)
        else:
            # Fallback for future services
            return adapter_class(**merged_config)

    @classmethod
    def _create_github_adapter(cls, config: Dict[str, Any]) -> MCPGitHubAdapter:
        """Create GitHub adapter with configuration."""
        # Get GitHub token from config or environment
        access_token = (
            config.get("access_token")
            or config.get("github_token")
            or os.getenv("GITHUB_TOKEN")
            or os.getenv("GITHUB_ACCESS_TOKEN")
        )

        if not access_token:
            logger.warning("No GitHub access token provided. Some operations may fail.")

        # Create merged config with access_token
        merged_config = config.copy()
        if access_token:
            merged_config["access_token"] = access_token

        return MCPGitHubAdapter(merged_config)

    @classmethod
    def _create_forgejo_adapter(cls, config: Dict[str, Any]) -> MCPForgejoAdapter:
        """Create Forgejo adapter with configuration."""
        # Get Forgejo base URL (required)
        base_url = config.get("base_url") or os.getenv("FORGEJO_BASE_URL")
        if not base_url:
            raise KeyError("Forgejo base_url is required")

        # Get authentication credentials
        access_token = (
            config.get("access_token")
            or config.get("forgejo_token")
            or os.getenv("FORGEJO_TOKEN")
            or os.getenv("FORGEJO_ACCESS_TOKEN")
        )

        username = (
            config.get("username")
            or config.get("forgejo_username")
            or os.getenv("FORGEJO_USERNAME")
        )

        password = (
            config.get("password")
            or config.get("forgejo_password")
            or os.getenv("FORGEJO_PASSWORD")
        )

        if not access_token and not (username and password):
            logger.warning(
                "No Forgejo authentication credentials provided. "
                "Some operations may fail."
            )

        # Create merged config with all detected values
        merged_config = config.copy()
        if base_url:
            merged_config["base_url"] = base_url
        if access_token:
            merged_config["access_token"] = access_token
        if username:
            merged_config["username"] = username
        if password:
            merged_config["password"] = password

        return MCPForgejoAdapter(merged_config)

    @classmethod
    def create_from_repository_context(
        cls,
        repository_context: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> MCPGitToolsBase:
        """
        Create a Git tools adapter from repository context.

        Args:
            repository_context: Repository context containing service information
            config: Additional service configuration
            **kwargs: Additional configuration parameters

        Returns:
            MCPGitToolsBase: Configured Git tools adapter

        Raises:
            ValueError: If repository context is invalid
        """
        service_type = repository_context.get("service")
        if not service_type:
            raise ValueError("Repository context must contain 'service' field")

        # Extract service-specific configuration from context
        context_config = {}
        if service_type == "forgejo":
            # Extract base URL from context if available
            if "base_url" in repository_context:
                context_config["base_url"] = repository_context["base_url"]
            elif "forgejo_base_url" in repository_context:
                context_config["base_url"] = repository_context["forgejo_base_url"]

        # Merge configurations
        merged_config = {}
        if config:
            merged_config.update(config)
        merged_config.update(context_config)
        merged_config.update(kwargs)

        return cls.create(service_type, merged_config)

    @classmethod
    def get_supported_services(cls) -> List[str]:
        """Get list of supported Git services."""
        return list(cls._adapters.keys())

    @classmethod
    def register_adapter(
        cls, service_type: str, adapter_class: Type[MCPGitToolsBase]
    ) -> None:
        """
        Register a new Git tools adapter.

        Args:
            service_type: Type of Git service
            adapter_class: Adapter class to register
        """
        if not issubclass(adapter_class, MCPGitToolsBase):
            raise TypeError("Adapter class must inherit from MCPGitToolsBase")

        cls._adapters[service_type] = adapter_class
        logger.info(f"Registered Git tools adapter for service: {service_type}")


# Convenience functions for common use cases
def create_github_tools(
    access_token: Optional[str] = None, **kwargs
) -> MCPGitToolsBase:
    """
    Create GitHub MCP tools adapter.

    Args:
        access_token: GitHub access token
        **kwargs: Additional configuration

    Returns:
        MCPGitHubAdapter: Configured GitHub adapter
    """
    return MCPGitToolsFactory.create("github", access_token=access_token, **kwargs)


def create_forgejo_tools(
    base_url: str,
    access_token: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    **kwargs,
) -> MCPGitToolsBase:
    """
    Create Forgejo MCP tools adapter.

    Args:
        base_url: Forgejo instance base URL
        access_token: Forgejo access token
        username: Username for basic auth
        password: Password for basic auth
        **kwargs: Additional configuration

    Returns:
        MCPForgejoAdapter: Configured Forgejo adapter
    """
    return MCPGitToolsFactory.create(
        "forgejo",
        base_url=base_url,
        access_token=access_token,
        username=username,
        password=password,
        **kwargs,
    )
