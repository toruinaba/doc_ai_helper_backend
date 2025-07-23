"""
Function Validation (Function Validation)

LLMサービス向けのFunction Call検証ユーティリティを提供します。

主要機能:
- 関数引数の検証
- 関数実行の安全性保証
- エラーハンドリング
"""

import json
import logging
from typing import Dict, Any, Callable

from doc_ai_helper_backend.models.llm import FunctionDefinition, FunctionCall

logger = logging.getLogger(__name__)


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
