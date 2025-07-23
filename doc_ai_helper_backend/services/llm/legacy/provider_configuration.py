"""
Provider configuration service for LLM providers.

This module provides centralized configuration management for LLM providers,
eliminating duplication and providing a single source of truth for provider setup.
"""

import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.services.llm.factory import LLMServiceFactory
from doc_ai_helper_backend.core.exceptions import ServiceNotFoundError, LLMServiceException

logger = logging.getLogger(__name__)


class ProviderConfig(ABC):
    """Abstract base class for provider configuration."""
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Get provider-specific configuration."""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate that the provider is properly configured."""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name."""
        pass


class OpenAIConfig(ProviderConfig):
    """Configuration for OpenAI provider."""
    
    def __init__(self):
        """Initialize OpenAI configuration."""
        from doc_ai_helper_backend.core.config import settings
        self.settings = settings
    
    def get_config(self) -> Dict[str, Any]:
        """Get OpenAI-specific configuration."""
        config = {}
        
        if self.settings.openai_api_key:
            config["api_key"] = self.settings.openai_api_key
        
        if self.settings.default_openai_model:
            config["default_model"] = self.settings.default_openai_model
        
        if self.settings.openai_base_url:
            config["base_url"] = self.settings.openai_base_url
        
        return config
    
    def validate_config(self) -> bool:
        """Validate OpenAI configuration."""
        if not self.settings.openai_api_key:
            logger.warning("OpenAI API key not configured")
            return False
        
        return True
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "openai"


class MockConfig(ProviderConfig):
    """Configuration for Mock provider."""
    
    def get_config(self) -> Dict[str, Any]:
        """Get Mock-specific configuration."""
        return {
            "default_model": "mock-model",
            "response_delay": 0.1,  # Small delay to simulate API calls
        }
    
    def validate_config(self) -> bool:
        """Validate Mock configuration."""
        # Mock provider is always available
        return True
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "mock"


class ProviderConfigurationService:
    """
    Centralized provider configuration management service.
    
    This service handles configuration for all LLM providers, providing
    a consistent interface for provider setup and validation.
    """
    
    def __init__(self):
        """Initialize the provider configuration service."""
        self._provider_configs: Dict[str, ProviderConfig] = {
            "openai": OpenAIConfig(),
            "mock": MockConfig(),
        }
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """
        Get provider-specific configuration from environment.
        
        Args:
            provider: Name of the provider
            
        Returns:
            Dict[str, Any]: Provider configuration
            
        Raises:
            ServiceNotFoundError: If provider is not supported
        """
        provider = provider.lower()
        
        if provider not in self._provider_configs:
            available_providers = list(self._provider_configs.keys())
            raise ServiceNotFoundError(
                f"Provider '{provider}' not supported. Available providers: {available_providers}"
            )
        
        provider_config = self._provider_configs[provider]
        config = provider_config.get_config()
        
        logger.debug(f"Retrieved configuration for provider '{provider}'")
        return config
    
    def validate_provider_availability(self, provider: str) -> bool:
        """
        Check if provider is properly configured and available.
        
        Args:
            provider: Name of the provider
            
        Returns:
            bool: True if provider is available
        """
        provider = provider.lower()
        
        if provider not in self._provider_configs:
            logger.warning(f"Provider '{provider}' not supported")
            return False
        
        provider_config = self._provider_configs[provider]
        is_valid = provider_config.validate_config()
        
        if not is_valid:
            logger.warning(f"Provider '{provider}' configuration is invalid")
        
        return is_valid
    
    def create_service_with_config(
        self, 
        provider: str, 
        enable_mcp: bool = True,
        additional_config: Optional[Dict[str, Any]] = None
    ) -> LLMServiceBase:
        """
        Create configured LLM service instance.
        
        Args:
            provider: Name of the provider
            enable_mcp: Whether to enable MCP integration
            additional_config: Additional configuration to merge
            
        Returns:
            LLMServiceBase: Configured service instance
            
        Raises:
            ServiceNotFoundError: If provider is not supported
            LLMServiceException: If service creation fails
        """
        # Validate provider availability
        if not self.validate_provider_availability(provider):
            raise LLMServiceException(
                message=f"Provider '{provider}' is not properly configured or available"
            )
        
        # Get base configuration
        config = self.get_provider_config(provider)
        
        # Merge additional configuration if provided
        if additional_config:
            config.update(additional_config)
        
        # Create service instance
        try:
            if enable_mcp:
                service = LLMServiceFactory.create_with_mcp(provider, **config)
            else:
                service = LLMServiceFactory.create(provider, **config)
            
            logger.info(f"Successfully created LLM service for provider: {provider}")
            return service
            
        except Exception as e:
            logger.error(f"Failed to create LLM service for provider '{provider}': {e}")
            raise LLMServiceException(
                message=f"Failed to create service for provider '{provider}'",
                detail=str(e)
            )
    
    def get_available_providers(self) -> List[str]:
        """
        Get list of available and properly configured providers.
        
        Returns:
            List[str]: List of available provider names
        """
        available = []
        
        for provider_name in self._provider_configs.keys():
            if self.validate_provider_availability(provider_name):
                available.append(provider_name)
        
        return available
    
    def get_all_supported_providers(self) -> List[str]:
        """
        Get list of all supported providers (regardless of configuration status).
        
        Returns:
            List[str]: List of all supported provider names
        """
        return list(self._provider_configs.keys())
    
    def get_provider_status(self, provider: str) -> Dict[str, Any]:
        """
        Get detailed status information for a provider.
        
        Args:
            provider: Name of the provider
            
        Returns:
            Dict[str, Any]: Provider status information
        """
        provider = provider.lower()
        
        if provider not in self._provider_configs:
            return {
                "provider": provider,
                "supported": False,
                "configured": False,
                "available": False,
                "error": "Provider not supported"
            }
        
        provider_config = self._provider_configs[provider]
        is_configured = provider_config.validate_config()
        
        status = {
            "provider": provider,
            "supported": True,
            "configured": is_configured,
            "available": is_configured,
        }
        
        if not is_configured:
            status["error"] = f"Provider '{provider}' is not properly configured"
        
        # Add configuration details (without sensitive information)
        config = provider_config.get_config()
        safe_config = {}
        
        for key, value in config.items():
            if "key" in key.lower() or "token" in key.lower():
                # Hide sensitive information
                safe_config[key] = "***" if value else None
            else:
                safe_config[key] = value
        
        status["config"] = safe_config
        
        return status
    
    def register_provider_config(self, provider_config: ProviderConfig) -> None:
        """
        Register a new provider configuration.
        
        Args:
            provider_config: Provider configuration instance
        """
        provider_name = provider_config.get_provider_name().lower()
        self._provider_configs[provider_name] = provider_config
        logger.info(f"Registered provider configuration: {provider_name}")
    
    def get_provider_capabilities_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get capabilities summary for all available providers.
        
        Returns:
            Dict[str, Dict[str, Any]]: Provider capabilities by provider name
        """
        capabilities = {}
        
        for provider_name in self.get_available_providers():
            try:
                service = self.create_service_with_config(provider_name, enable_mcp=False)
                # Note: This is async, so we'd need to handle this differently in practice
                # For now, just include basic info
                capabilities[provider_name] = {
                    "available": True,
                    "service_created": True,
                }
            except Exception as e:
                capabilities[provider_name] = {
                    "available": False,
                    "error": str(e),
                }
        
        return capabilities


# Global instance for easy access
provider_config_service = ProviderConfigurationService()