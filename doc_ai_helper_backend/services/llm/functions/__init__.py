"""
Functions subpackage for LLM services.
Handles all function calling and execution functionality.
"""

from .functions import (
    FunctionRegistry,
    FunctionCallManager,
    FunctionService,
    validate_function_call_arguments,
    execute_function_safely,
    convert_function_definition_to_openai_tool,
    parse_openai_tool_calls,
    get_utility_functions,
    default_function_call_manager,
)

__all__ = [
    "FunctionRegistry",
    "FunctionCallManager",
    "FunctionService",
    "validate_function_call_arguments",
    "execute_function_safely",
    "convert_function_definition_to_openai_tool",
    "parse_openai_tool_calls",
    "get_utility_functions",
    "default_function_call_manager",
]
