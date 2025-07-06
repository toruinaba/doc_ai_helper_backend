"""
Mixin classes for LLM services.

This module provides mixin classes that can be used to add common functionality
to LLM service implementations without inheritance complexity.
"""

from typing import TYPE_CHECKING, Dict, Any, Optional

if TYPE_CHECKING:
    from doc_ai_helper_backend.services.llm.common import LLMServiceCommon
    from doc_ai_helper_backend.services.llm.utils import (
        PromptTemplateManager,
        LLMCacheService,
        JapaneseSystemPromptBuilder,
        FunctionCallManager,
        LLMResponseBuilder,
        StreamingUtils,
    )


class CommonPropertyAccessors:
    """
    Mixin class providing common property accessors for LLM services.

    This class assumes that the implementing class has a `_common` attribute
    that is an instance of LLMServiceCommon.
    """

    _common: "LLMServiceCommon"  # Type hint for the common instance

    @property
    def cache_service(self) -> "LLMCacheService":
        """Get the cache service from common implementation."""
        return self._common.cache_service

    @property
    def template_manager(self) -> "PromptTemplateManager":
        """Get the template manager from common implementation."""
        return self._common.template_manager

    @property
    def function_manager(self) -> "FunctionCallManager":
        """Get the function manager from common implementation."""
        return self._common.function_manager

    @property
    def system_prompt_builder(self) -> "JapaneseSystemPromptBuilder":
        """Get the system prompt builder from common implementation."""
        return self._common.system_prompt_builder

    @property
    def response_builder(self) -> "LLMResponseBuilder":
        """Get the response builder from common implementation."""
        return self._common.response_builder

    @property
    def streaming_utils(self) -> "StreamingUtils":
        """Get the streaming utils from common implementation."""
        return self._common.streaming_utils

    @property
    def mcp_adapter(self):
        """Get the MCP adapter from common implementation."""
        return self._common.get_mcp_adapter()

    # === MCP adapter methods (delegated to common) ===

    def set_mcp_adapter(self, adapter):
        """Set the MCP adapter through common implementation."""
        self._common.set_mcp_adapter(adapter)

    def get_mcp_adapter(self):
        """Get the MCP adapter from common implementation."""
        return self._common.get_mcp_adapter()


class BackwardCompatibilityAccessors:
    """
    Mixin class providing backward compatibility property accessors.

    This class provides aliases for properties that may have been renamed
    or restructured, maintaining compatibility with existing code.
    """

    _common: "LLMServiceCommon"  # Type hint for the common instance

    @property
    def function_handler(self):
        """Access to function handler for backward compatibility."""
        return self._common.function_manager

    # Add other backward compatibility properties as needed


class ErrorHandlingMixin:
    """
    Mixin providing common error handling patterns.

    This mixin provides standardized error handling methods that can be
    used across different LLM service implementations.
    """

    def _handle_api_error(self, error: Exception, context: str = "") -> Exception:
        """
        Handle API errors with standardized error conversion.

        Args:
            error: The original error
            context: Additional context for the error

        Returns:
            Exception: Standardized exception
        """
        from doc_ai_helper_backend.core.exceptions import LLMServiceException

        error_msg = f"{context}: {str(error)}" if context else str(error)
        return LLMServiceException(error_msg)

    def _validate_required_params(self, **kwargs) -> None:
        """
        Validate that required parameters are present.

        Args:
            **kwargs: Parameters to validate (param_name: param_value)

        Raises:
            LLMServiceException: If any required parameter is missing
        """
        from doc_ai_helper_backend.core.exceptions import LLMServiceException

        missing_params = [name for name, value in kwargs.items() if value is None]
        if missing_params:
            raise LLMServiceException(
                f"Missing required parameters: {', '.join(missing_params)}"
            )


class ConfigurationMixin:
    """
    Mixin providing common configuration management.

    This mixin provides standardized configuration handling that can be
    shared across different LLM service implementations.
    """

    def _merge_options(
        self,
        base_options: Dict[str, Any],
        override_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Merge base options with override options.

        Args:
            base_options: Base configuration options
            override_options: Options to override base options

        Returns:
            Dict[str, Any]: Merged options
        """
        if override_options is None:
            return base_options.copy()

        merged = base_options.copy()
        merged.update(override_options)
        return merged

    def _extract_common_params(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract common parameters from options.

        Args:
            options: Options dictionary

        Returns:
            Dict[str, Any]: Common parameters
        """
        common_params = {}

        # Standard parameter mapping
        param_mapping = {
            "model": "model",
            "temperature": "temperature",
            "max_tokens": "max_tokens",
            "top_p": "top_p",
            "frequency_penalty": "frequency_penalty",
            "presence_penalty": "presence_penalty",
            "stop": "stop",
            "stream": "stream",
        }

        for option_key, param_key in param_mapping.items():
            if option_key in options:
                common_params[param_key] = options[option_key]

        return common_params


class ServicePropertyMixin:
    """
    Mixin providing service-specific property management.

    This mixin helps LLM services manage their own properties while
    maintaining compatibility with common property accessors.
    """

    def __init__(self):
        # Initialize common attributes that will be set by the implementing class
        self._model = None
        self._temperature = None
        self._max_tokens = None
        self._default_options = {}

    @property
    def model(self) -> Optional[str]:
        """Get the default model."""
        return getattr(self, "_model", None) or getattr(self, "default_model", None)

    @property
    def temperature(self) -> Optional[float]:
        """Get the default temperature."""
        return getattr(self, "_temperature", None) or getattr(
            self, "default_temperature", None
        )

    @property
    def max_tokens(self) -> Optional[int]:
        """Get the default max tokens."""
        return getattr(self, "_max_tokens", None) or getattr(
            self, "default_max_tokens", None
        )

    @property
    def default_options(self) -> Dict[str, Any]:
        """Get the default options."""
        return getattr(self, "_default_options", {})

    @property
    def api_key(self) -> Optional[str]:
        """Get the API key (backward compatibility)."""
        return getattr(self, "_api_key", None)

    @property
    def base_url(self) -> Optional[str]:
        """Get the base URL (backward compatibility)."""
        return getattr(self, "_base_url", None)

    @property
    def organization(self) -> Optional[str]:
        """Get the organization (backward compatibility)."""
        return getattr(self, "_organization", None)
