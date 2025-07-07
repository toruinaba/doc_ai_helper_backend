"""
LLM utility modules.

This package provides utility functions and classes for LLM services,
organized by functionality for better maintainability.

Note: Many utilities have been migrated to the components package for better
organization. This module now provides backward compatibility imports.
"""

# Backward compatibility imports from new structure
from ..messaging.messaging import (
    summarize_conversation_history,
    format_conversation_for_provider,
    SystemPromptCache,
    SystemPromptBuilder,
)

# Template utilities
from ..processing.templates import PromptTemplateManager

# Caching utilities
from ..processing.cache import LLMCacheService

# Function calling utilities
from ..functions.functions import (
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
from ..processing.tokens import (
    estimate_message_tokens,
    estimate_conversation_tokens,
    estimate_tokens_for_messages,
    optimize_conversation_history,
)

# Response building utilities
from ..processing.response_builder import LLMResponseBuilder

# Streaming utilities
from ..processing.streaming_utils import StreamingUtils

# Query orchestration utilities (backward compatibility)
from ..query_manager import QueryManager as QueryOrchestrator

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
    # Query orchestration
    "QueryOrchestrator",
    # Simulation
    "SimulationUtils",
]
