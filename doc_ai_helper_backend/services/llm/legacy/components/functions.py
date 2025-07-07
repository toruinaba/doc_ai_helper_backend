"""
Function Calling サービス (Function Calling Service)

LLMサービス向けのFunction Calling機能を提供します。
元ファイル: utils/functions.py

このコンポーネントは純粋な委譲パターンで使用され、mixin継承は使用しません。

主要機能:
- 関数レジストリの管理
- Function Callingの実行
- ツール呼び出しの処理
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
    LLM Function Calling用の関数レジストリ管理クラス
    """

    def __init__(self):
        """関数レジストリの初期化"""
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
        LLM Function Calling用の関数を登録

        Args:
            name: 関数名
            function: 実行可能な関数
            description: 関数の説明
            parameters: 関数のパラメータスキーマ
        """
        self._functions[name] = function
        self._function_definitions[name] = FunctionDefinition(
            name=name,
            description=description or f"Function {name}",
            parameters=parameters
            or {"type": "object", "properties": {}, "required": []},
        )

    def unregister_function(self, name: str) -> bool:
        """
        関数の登録を解除

        Args:
            name: 関数名

        Returns:
            bool: 解除が成功した場合True
        """
        if name in self._functions:
            del self._functions[name]
            del self._function_definitions[name]
            return True
        return False

    def get_function(self, name: str) -> Optional[Callable]:
        """
        登録された関数を取得

        Args:
            name: 関数名

        Returns:
            Optional[Callable]: 関数（見つからない場合はNone）
        """
        return self._functions.get(name)

    def get_function_definition(self, name: str) -> Optional[FunctionDefinition]:
        """
        関数定義を取得

        Args:
            name: 関数名

        Returns:
            Optional[FunctionDefinition]: 関数定義（見つからない場合はNone）
        """
        return self._function_definitions.get(name)

    def list_functions(self) -> List[str]:
        """
        登録されている関数のリストを取得

        Returns:
            List[str]: 関数名のリスト
        """
        return list(self._functions.keys())

    def get_all_definitions(self) -> List[FunctionDefinition]:
        """
        すべての関数定義を取得

        Returns:
            List[FunctionDefinition]: 関数定義のリスト
        """
        return list(self._function_definitions.values())

    def clear(self) -> None:
        """すべての関数を削除"""
        self._functions.clear()
        self._function_definitions.clear()

    def get_all_function_definitions(self) -> List[FunctionDefinition]:
        """
        すべての関数定義を取得（後方互換性のため）

        Returns:
            List[FunctionDefinition]: 関数定義のリスト
        """
        return self.get_all_definitions()

    def get_all_functions(self) -> Dict[str, Callable]:
        """
        すべての登録済み関数を取得

        Returns:
            Dict[str, Callable]: 関数名→関数のマッピング
        """
        return self._functions.copy()


class FunctionService:
    """
    Function Calling サービスクラス

    関数レジストリの管理と関数実行を提供します。
    """

    def __init__(self):
        """Function Calling サービスの初期化"""
        self.registry = FunctionRegistry()

    def register_function(
        self,
        name: str,
        function: Callable,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """関数を登録（レジストリに委譲）"""
        self.registry.register_function(name, function, description, parameters)

    def execute_function_call(self, function_call: FunctionCall) -> Any:
        """
        関数呼び出しを実行

        Args:
            function_call: 実行する関数呼び出し

        Returns:
            Any: 関数の実行結果

        Raises:
            ValueError: 関数が見つからない場合
            Exception: 関数実行中にエラーが発生した場合
        """
        function = self.registry.get_function(function_call.name)
        if not function:
            raise ValueError(f"Function '{function_call.name}' not found")

        try:
            # 引数をパース
            if isinstance(function_call.arguments, str):
                arguments = json.loads(function_call.arguments)
            else:
                arguments = function_call.arguments or {}

            # 関数を実行
            result = function(**arguments)
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse function arguments: {e}")
            raise ValueError(f"Invalid function arguments: {e}")
        except Exception as e:
            logger.error(f"Function execution failed: {e}")
            raise

    def execute_tool_calls(self, tool_calls: List[ToolCall]) -> List[Dict[str, Any]]:
        """
        複数のツール呼び出しを実行

        Args:
            tool_calls: 実行するツール呼び出しのリスト

        Returns:
            List[Dict[str, Any]]: 各ツール呼び出しの結果
        """
        results = []

        for tool_call in tool_calls:
            try:
                if tool_call.type == "function" and tool_call.function:
                    result = self.execute_function_call(tool_call.function)
                    results.append(
                        {
                            "tool_call_id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "result": result,
                            },
                        }
                    )
                else:
                    results.append(
                        {
                            "tool_call_id": tool_call.id,
                            "type": "error",
                            "error": f"Unsupported tool call type: {tool_call.type}",
                        }
                    )
            except Exception as e:
                results.append(
                    {"tool_call_id": tool_call.id, "type": "error", "error": str(e)}
                )

        return results

    def get_available_functions(self) -> List[FunctionDefinition]:
        """
        利用可能な関数定義のリストを取得

        Returns:
            List[FunctionDefinition]: 関数定義のリスト
        """
        return self.registry.get_all_definitions()

    def prepare_functions_for_api(
        self, function_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        API用の関数定義を準備

        Args:
            function_names: 使用する関数名のリスト（Noneの場合はすべて）

        Returns:
            List[Dict[str, Any]]: API用関数定義のリスト
        """
        if function_names is None:
            definitions = self.registry.get_all_definitions()
        else:
            definitions = [
                self.registry.get_function_definition(name)
                for name in function_names
                if self.registry.get_function_definition(name) is not None
            ]

        return [
            {
                "type": "function",
                "function": {
                    "name": definition.name,
                    "description": definition.description,
                    "parameters": definition.parameters,
                },
            }
            for definition in definitions
            if definition
        ]

    def validate_function_call(self, function_call: FunctionCall) -> bool:
        """
        関数呼び出しの妥当性を検証

        Args:
            function_call: 検証する関数呼び出し

        Returns:
            bool: 妥当な場合True
        """
        # 関数が存在するかチェック
        if not self.registry.get_function(function_call.name):
            return False

        # 引数が有効なJSONかチェック
        try:
            if isinstance(function_call.arguments, str):
                json.loads(function_call.arguments)
        except json.JSONDecodeError:
            return False

        return True

    def create_tool_choice(
        self, choice_type: str = "auto", function_name: Optional[str] = None
    ) -> ToolChoice:
        """
        ツール選択オプションを作成

        Args:
            choice_type: 選択タイプ（"auto", "none", "required"）
            function_name: 特定の関数を指定する場合の関数名

        Returns:
            ToolChoice: ツール選択オプション
        """
        if choice_type == "auto":
            return ToolChoice(type="auto")
        elif choice_type == "none":
            return ToolChoice(type="none")
        elif choice_type == "required":
            return ToolChoice(type="required")
        elif choice_type == "function" and function_name:
            return ToolChoice(type="function", function={"name": function_name})
        else:
            return ToolChoice(type="auto")


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
