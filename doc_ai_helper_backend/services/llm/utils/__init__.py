"""
LLM utility modules.

This package provides utility functions and classes for LLM services,
organized by functionality for better maintainability.
"""

# Messaging utilities (conversation history, system prompts)
from .messaging import (
    summarize_conversation_history,
    format_conversation_for_provider,
)

# Template utilities
from .templating import PromptTemplateManager

# Caching utilities
from .caching import LLMCacheService

# Function calling utilities
from .functions import (
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
from .tokens import (
    estimate_message_tokens,
    estimate_conversation_tokens,
    estimate_tokens_for_messages,
    optimize_conversation_history,
)

# Helper utilities
from .helpers import (
    get_current_timestamp,
    safe_get_nested_value,
    truncate_text,
    sanitize_filename,
    deep_merge_dicts,
    DEFAULT_MAX_TOKENS,
    SystemPromptCache,
    SystemPromptBuilder,
    JapaneseSystemPromptBuilder,
)

__all__ = [
    # Messaging
    "optimize_conversation_history",
    "summarize_conversation_history",
    "format_conversation_for_provider",
    "SystemPromptBuilder",
    "SystemPromptCache",
    "JapaneseSystemPromptBuilder",
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
]
