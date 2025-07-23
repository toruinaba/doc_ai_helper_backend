"""
Function Registry (Function Registry)

LLMサービス向けのFunction Calling関数レジストリ管理を提供します。

主要機能:
- 関数レジストリの管理
- 関数定義の管理
"""

import logging
from typing import Dict, Any, List, Optional, Callable

from doc_ai_helper_backend.models.llm import FunctionDefinition

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
