"""
Function Service (Function Service)

LLMサービス向けのFunction Calling実行サービスを提供します。

主要機能:
- 関数呼び出しの実行
- ツール呼び出しの処理
- API用関数定義の準備
"""

import json
import logging
from typing import Dict, Any, List, Optional, Callable

from doc_ai_helper_backend.models.llm import (
    FunctionDefinition,
    FunctionCall,
    ToolCall,
    ToolChoice,
)
from .function_registry import FunctionRegistry

logger = logging.getLogger(__name__)


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
