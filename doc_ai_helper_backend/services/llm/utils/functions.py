"""
Function calling utilities for LLM services.

This module provides utilities for managing function calls, registries,
and function execution in LLM services.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Callable, Union

from doc_ai_helper_backend.models.llm import (
    FunctionDefinition,
    FunctionCall,
    ToolCall,
    ToolChoice,
)

logger = logging.getLogger(__name__)


class FunctionRegistry:
    """
    Registry for managing available functions for LLM function calling.
    """

    def __init__(self):
        """Initialize the function registry."""
        self._functions: Dict[str, Callable] = {}
        self._function_definitions: Dict[str, FunctionDefinition] = {}

    def register_function(
        self,
        name: str,
        function: Callable,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Register a function for LLM function calling.

        Args:
            name: Function name
            function: The callable function
            description: Function description
            parameters: Function parameters schema
        """
        self._functions[name] = function
        self._function_definitions[name] = FunctionDefinition(
            name=name,
            description=description or f"Function {name}",
            parameters=parameters or {"type": "object", "properties": {}},
        )
        logger.info(f"Registered function: {name}")

    def unregister_function(self, name: str) -> None:
        """
        Unregister a function.

        Args:
            name: Function name to unregister
        """
        if name in self._functions:
            del self._functions[name]
            del self._function_definitions[name]
            logger.info(f"Unregistered function: {name}")

    def get_function(self, name: str) -> Optional[Callable]:
        """
        Get a registered function by name.

        Args:
            name: Function name

        Returns:
            Optional[Callable]: The function if found, None otherwise
        """
        return self._functions.get(name)

    def get_function_definition(self, name: str) -> Optional[FunctionDefinition]:
        """
        Get a function definition by name.

        Args:
            name: Function name

        Returns:
            Optional[FunctionDefinition]: The function definition if found, None otherwise
        """
        return self._function_definitions.get(name)

    def get_all_functions(self) -> Dict[str, Callable]:
        """
        Get all registered functions.

        Returns:
            Dict[str, Callable]: Dictionary of all functions
        """
        return self._functions.copy()

    def get_all_function_definitions(self) -> List[FunctionDefinition]:
        """
        Get all function definitions.

        Returns:
            List[FunctionDefinition]: List of all function definitions
        """
        return list(self._function_definitions.values())

    def clear(self) -> None:
        """Clear all registered functions."""
        self._functions.clear()
        self._function_definitions.clear()
        logger.info("Cleared all registered functions")


class FunctionCallManager:
    """
    Manager for handling function calls in LLM responses.
    """

    def __init__(self, function_registry: Optional[FunctionRegistry] = None):
        """
        Initialize the function call manager.

        Args:
            function_registry: Registry of available functions
        """
        self.function_registry = function_registry or FunctionRegistry()

    async def execute_function_call(
        self, function_call: FunctionCall
    ) -> Dict[str, Any]:
        """
        Execute a function call from an LLM response.

        Args:
            function_call: The function call to execute

        Returns:
            Dict[str, Any]: The result of the function execution
        """
        try:
            # 関数定義を取得
            function_def = self.function_registry.get_function_definition(
                function_call.name
            )
            if not function_def:
                return {
                    "success": False,
                    "error": f"Function '{function_call.name}' not found",
                    "result": None,
                }

            # 引数をパース
            try:
                arguments = json.loads(function_call.arguments)
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Invalid JSON in function arguments: {str(e)}",
                    "result": None,
                }

            # 引数を検証（パース済み引数を使用）
            if not validate_parsed_function_arguments(
                arguments, function_call.name, function_def
            ):
                return {
                    "success": False,
                    "error": f"Invalid arguments for function '{function_call.name}'",
                    "result": None,
                }

            # 関数を実行
            return execute_function_safely(
                function_call.name,
                arguments,
                self.function_registry.get_all_functions(),
            )

        except Exception as e:
            logger.error(f"Error executing function call: {e}")
            return {
                "success": False,
                "error": f"Execution error: {str(e)}",
                "result": None,
            }

    async def execute_tool_calls(
        self, tool_calls: List[ToolCall]
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tool calls from an LLM response.

        Args:
            tool_calls: List of tool calls to execute

        Returns:
            List[Dict[str, Any]]: List of execution results
        """
        results = []
        for tool_call in tool_calls:
            if tool_call.type == "function":
                result = await self.execute_function_call(tool_call.function)
                results.append(
                    {
                        "tool_call_id": tool_call.id,
                        "result": result,
                    }
                )
            else:
                results.append(
                    {
                        "tool_call_id": tool_call.id,
                        "result": {
                            "success": False,
                            "error": f"Unsupported tool type: {tool_call.type}",
                            "result": None,
                        },
                    }
                )
        return results

    def register_function(
        self,
        name: str,
        function: Callable,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Register a function for function calling.

        Args:
            name: Function name
            function: The callable function
            description: Function description
            parameters: Function parameters schema
        """
        self.function_registry.register_function(
            name, function, description, parameters
        )

    def get_available_functions(self) -> List[FunctionDefinition]:
        """
        Get all available function definitions.

        Returns:
            List[FunctionDefinition]: List of available function definitions
        """
        return self.function_registry.get_all_function_definitions()


# Function call validation and execution utilities


def validate_parsed_function_arguments(
    arguments: Dict[str, Any],
    function_name: str,
    function_definition: FunctionDefinition,
) -> bool:
    """
    パース済みの引数が関数定義に適合するかを検証する。

    Args:
        arguments: パース済みの引数辞書
        function_name: 関数名
        function_definition: 関数定義

    Returns:
        bool: 引数が有効かどうか
    """
    try:
        # 関数名の確認
        if function_name != function_definition.name:
            logger.warning(
                f"Function name mismatch: {function_name} != {function_definition.name}"
            )
            return False

        # パラメータ定義がない場合は引数も空である必要がある
        if not function_definition.parameters:
            return len(arguments) == 0

        # 必須パラメータの確認
        required_params = function_definition.parameters.get("required", [])
        for param in required_params:
            if param not in arguments:
                logger.warning(f"Required parameter missing: {param}")
                return False

        # 未知のパラメータの確認
        properties = function_definition.parameters.get("properties", {})
        for param in arguments:
            if param not in properties:
                logger.warning(f"Unknown parameter: {param}")
                return False

        return True

    except Exception as e:
        logger.error(f"Error validating function call arguments: {e}")
        return False


def validate_function_call_arguments(
    function_call: FunctionCall, function_definition: FunctionDefinition
) -> bool:
    """
    Function callの引数が関数定義に適合するかを検証する。

    Args:
        function_call: LLMからのFunction call
        function_definition: 関数定義

    Returns:
        bool: 引数が有効かどうか
    """
    try:
        # 引数をJSONとしてパース
        arguments = json.loads(function_call.arguments)

        # 関数名の確認
        if function_call.name != function_definition.name:
            logger.warning(
                f"Function name mismatch: {function_call.name} != {function_definition.name}"
            )
            return False

        # パラメータ定義がない場合は引数も空である必要がある
        if not function_definition.parameters:
            return len(arguments) == 0

        # 必須パラメータの確認
        required_params = function_definition.parameters.get("required", [])
        for param in required_params:
            if param not in arguments:
                logger.warning(f"Required parameter missing: {param}")
                return False

        # 未知のパラメータの確認
        properties = function_definition.parameters.get("properties", {})
        for param in arguments:
            if param not in properties:
                logger.warning(f"Unknown parameter: {param}")
                return False

        return True

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in function arguments: {e}")
        return False
    except Exception as e:
        logger.error(f"Error validating function call arguments: {e}")
        return False


def execute_function_safely(
    function_name: str, arguments: Dict[str, Any], available_functions: Dict[str, Any]
) -> Dict[str, Any]:
    """
    関数を安全に実行する。

    Args:
        function_name: 実行する関数名
        arguments: 関数の引数
        available_functions: 利用可能な関数の辞書

    Returns:
        Dict[str, Any]: 実行結果
    """
    try:
        if function_name not in available_functions:
            return {
                "success": False,
                "error": f"Function '{function_name}' not found",
                "result": None,
            }

        function = available_functions[function_name]

        # 関数が呼び出し可能かチェック
        if not callable(function):
            return {
                "success": False,
                "error": f"'{function_name}' is not callable",
                "result": None,
            }

        # 関数を実行
        result = function(**arguments)

        return {"success": True, "error": None, "result": result}

    except TypeError as e:
        logger.error(f"TypeError executing function {function_name}: {e}")
        return {
            "success": False,
            "error": f"Invalid arguments for function '{function_name}': {str(e)}",
            "result": None,
        }
    except Exception as e:
        logger.error(f"Error executing function {function_name}: {e}")
        return {"success": False, "error": f"Execution error: {str(e)}", "result": None}


# Conversion and parsing utilities


def convert_function_definition_to_openai_tool(
    function_def: FunctionDefinition,
) -> Dict[str, Any]:
    """
    FunctionDefinitionをOpenAI tools形式に変換する。

    Args:
        function_def: 変換する関数定義

    Returns:
        Dict[str, Any]: OpenAI tools形式の辞書
    """
    return {
        "type": "function",
        "function": {
            "name": function_def.name,
            "description": function_def.description or "",
            "parameters": function_def.parameters
            or {"type": "object", "properties": {}},
        },
    }


def parse_openai_tool_calls(tool_calls: List[Any]) -> List[ToolCall]:
    """
    OpenAI APIからのtool callsをToolCallモデルに変換する。

    Args:
        tool_calls: OpenAI APIからのtool calls

    Returns:
        List[ToolCall]: 変換されたToolCallのリスト
    """
    result = []
    for tool_call in tool_calls:
        if hasattr(tool_call, "function"):
            function_call = FunctionCall(
                name=tool_call.function.name, arguments=tool_call.function.arguments
            )
            result.append(
                ToolCall(id=tool_call.id, type="function", function=function_call)
            )

    return result


# Utility function definitions


def get_utility_functions() -> List[FunctionDefinition]:
    """
    Get the list of utility function definitions for LLM function calling.

    Returns:
        List[FunctionDefinition]: List of utility function definitions
    """
    return [
        FunctionDefinition(
            name="get_current_time",
            description="Get the current date and time in the specified timezone and format. Use this when users ask about the current time, date, or want to know what time it is.",
            parameters={
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone to use (UTC, JST, EST, etc.)",
                        "default": "UTC",
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format (ISO, readable, timestamp)",
                        "enum": ["ISO", "readable", "timestamp"],
                        "default": "ISO",
                    },
                },
                "required": [],
            },
        ),
        FunctionDefinition(
            name="count_text_characters",
            description="Count characters in the provided text with various counting options. Use this when users want to analyze text length, word count, or character statistics.",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The text to analyze"},
                    "count_type": {
                        "type": "string",
                        "description": "Type of counting",
                        "enum": ["all", "no_spaces", "alphanumeric", "words", "lines"],
                        "default": "all",
                    },
                },
                "required": ["text"],
            },
        ),
        FunctionDefinition(
            name="validate_email_format",
            description="Validate if the provided string is a valid email format. Use this when users want to check if an email address is properly formatted.",
            parameters={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Email address to validate",
                    }
                },
                "required": ["email"],
            },
        ),
        FunctionDefinition(
            name="generate_random_data",
            description="Generate random data for testing purposes. Use this when users need sample data, random strings, numbers, or test data.",
            parameters={
                "type": "object",
                "properties": {
                    "data_type": {
                        "type": "string",
                        "description": "Type of data to generate",
                        "enum": ["string", "number", "uuid", "password"],
                        "default": "string",
                    },
                    "length": {
                        "type": "integer",
                        "description": "Length of generated data",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 10,
                    },
                },
                "required": [],
            },
        ),
        FunctionDefinition(
            name="calculate_simple_math",
            description="Calculate simple mathematical expressions safely. Use this when users want to perform calculations or evaluate mathematical expressions.",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '2+3*4', '(10-5)*2')",
                    }
                },
                "required": ["expression"],
            },
        ),
    ]


# デフォルトのFunction Call Manager インスタンス
default_function_call_manager = FunctionCallManager()
