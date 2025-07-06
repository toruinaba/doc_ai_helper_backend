"""
LLM utility modules.

This package provides utility functions and classes for LLM services,
organized by functionality for better maintainability.

Note: Many utilities have been migrated to the components package for better
organization. This module now provides backward compatibility imports.
"""

# Backward compatibility imports from components
from ..components.messaging import (
    summarize_conversation_history,
    format_conversation_for_provider,
    SystemPromptCache,
    SystemPromptBuilder,
)

# Template utilities
from ..components.templates import PromptTemplateManager

# Caching utilities
from ..components.cache import LLMCacheService

# Function calling utilities
from ..components.functions import (
    FunctionRegistry,
    FunctionCallManager,
    validate_function_call_arguments,
    execute_function_safely,
    convert_function_definition_to_openai_tool,
    parse_openai_tool_calls,
    get_utility_functions,
    default_function_call_manager,
)

# Token utilities
from ..components.tokens import (
    estimate_message_tokens,
    estimate_conversation_tokens,
    estimate_tokens_for_messages,
    optimize_conversation_history,
)

# Response building utilities
from ..components.response_builder import LLMResponseBuilder

# Streaming utilities
from ..components.streaming_utils import StreamingUtils

# Property accessor mixins
from .mixins import (
    CommonPropertyAccessors,
    BackwardCompatibilityAccessors,
    ErrorHandlingMixin,
    ConfigurationMixin,
    ServiceDelegationMixin,
)

# Query orchestration utilities (backward compatibility)
from ..components.query_manager import QueryManager as QueryOrchestrator

# Simulation utilities
from .simulation import SimulationUtils

# Helper utilities
from .helpers import (
    get_current_timestamp,
    safe_get_nested_value,
    truncate_text,
    sanitize_filename,
    deep_merge_dicts,
    DEFAULT_MAX_TOKENS,
)

__all__ = [
    # Messaging
    "optimize_conversation_history",
    "summarize_conversation_history",
    "format_conversation_for_provider",
    "SystemPromptBuilder",
    "SystemPromptCache",
    # Templates
    "PromptTemplateManager",
    # Caching
    "LLMCacheService",
    # Functions
    "FunctionRegistry",
    "FunctionCallManager",
    "validate_function_call_arguments",
    "execute_function_safely",
    "convert_function_definition_to_openai_tool",
    "parse_openai_tool_calls",
    "get_utility_functions",
    "default_function_call_manager",
    # Tokens
    "estimate_message_tokens",
    "estimate_conversation_tokens",
    "estimate_tokens_for_messages",
    # Helpers
    "get_current_timestamp",
    "safe_get_nested_value",
    "truncate_text",
    "sanitize_filename",
    "deep_merge_dicts",
    "DEFAULT_MAX_TOKENS",
    # Response Building
    "LLMResponseBuilder",
    # Streaming
    "StreamingUtils",
    # Mixins
    "CommonPropertyAccessors",
    "BackwardCompatibilityAccessors",
    "ErrorHandlingMixin",
    "ConfigurationMixin",
    "ServiceDelegationMixin",
    # Query orchestration
    "QueryOrchestrator",
    # Simulation
    "SimulationUtils",
]
