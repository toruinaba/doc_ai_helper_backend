"""
Functions パッケージ - Function Calling機能

分割された各モジュールからの統一エクスポート：
- function_registry: FunctionRegistry クラス
- function_service: FunctionService クラス
- function_manager: FunctionCallManager クラス
- function_validation: バリデーション関数群
- function_utils: ユーティリティ関数群
"""

from .function_registry import FunctionRegistry
from .function_service import FunctionService
from .function_manager import FunctionCallManager
from .function_validation import (
    validate_parsed_function_arguments,
    validate_function_call_arguments,
    execute_function_safely,
)
from .function_utils import (
    convert_function_definition_to_openai_tool,
    parse_openai_tool_calls,
    get_utility_functions,
)

# デフォルトのFunction Call Manager インスタンス
default_function_call_manager = FunctionCallManager()

__all__ = [
    "FunctionRegistry",
    "FunctionService",
    "FunctionCallManager",
    "validate_parsed_function_arguments",
    "validate_function_call_arguments",
    "execute_function_safely",
    "convert_function_definition_to_openai_tool",
    "parse_openai_tool_calls",
    "get_utility_functions",
    "default_function_call_manager",
]
