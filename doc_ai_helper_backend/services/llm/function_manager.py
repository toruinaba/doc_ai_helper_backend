"""
Function calling manager for LLM services.

This module provides utilities for managing function calls in LLM services.
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
from doc_ai_helper_backend.services.llm.utils import (
    validate_function_call_arguments,
    execute_function_safely,
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

            # 引数を検証
            if not validate_function_call_arguments(function_call, function_def):
                return {
                    "success": False,
                    "error": f"Invalid arguments for function '{function_call.name}'",
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


# デフォルトのFunction Call Manager インスタンス
default_function_call_manager = FunctionCallManager()
