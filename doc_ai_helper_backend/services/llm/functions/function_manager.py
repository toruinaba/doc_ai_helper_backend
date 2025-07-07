"""
Function Call Manager (Function Call Manager)

LLMサービス向けのFunction Call実行管理を提供します。

主要機能:
- Function Callの実行管理
- Tool Callの実行管理
- 関数実行の安全性保証
"""

import json
import logging
from typing import Dict, Any, List, Optional, Callable

from doc_ai_helper_backend.models.llm import (
    FunctionDefinition,
    FunctionCall,
    ToolCall,
)
from .function_registry import FunctionRegistry

logger = logging.getLogger(__name__)


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
            # Import validation functions locally to avoid circular imports
            from .function_validation import (
                validate_parsed_function_arguments,
                execute_function_safely,
            )

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
