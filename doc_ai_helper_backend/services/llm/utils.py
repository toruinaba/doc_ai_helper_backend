"""
LLM utility functions.

This module provides utility functions for working with LLM services.
"""

from typing import Dict, Any, List, Optional, Tuple, Union, TYPE_CHECKING
import logging
from datetime import datetime

from doc_ai_helper_backend.models.llm import MessageItem, MessageRole

if TYPE_CHECKING:
    from doc_ai_helper_backend.models.llm import (
        FunctionCall,
        FunctionDefinition,
        ToolCall,
    )

logger = logging.getLogger(__name__)

# デフォルトのトークン限界値（OpenAI GPT-4: 8k）
DEFAULT_MAX_TOKENS = 8000


def estimate_message_tokens(
    message: Union[MessageItem, str], encoding_name: str = "cl100k_base"
) -> int:
    """
    単一のメッセージのおおよそのトークン数を推定する。

    Args:
        message: トークン数を推定するメッセージ
        encoding_name: 使用するエンコーディング名

    Returns:
        int: 推定トークン数
    """
    # messageが文字列の場合の処理
    if isinstance(message, str):
        try:
            import tiktoken
            encoding = tiktoken.get_encoding(encoding_name)
            return len(encoding.encode(message))
        except ImportError:
            logger.warning("tiktoken not available, using character approximation")
            return len(message) // 4
        except Exception as e:
            logger.warning(f"Failed to estimate tokens: {str(e)}")
            return len(message) // 4
    
    # messageがMessageItemオブジェクトでない場合の処理
    if not hasattr(message, 'content'):
        logger.warning(f"Invalid message object: {type(message)}")
        return 0

    try:
        import tiktoken

        encoding = tiktoken.get_encoding(encoding_name)
        # メッセージロールによるトークン数の調整
        role_tokens = 4  # 各メッセージには約4トークンのオーバーヘッドがある
        content_tokens = len(encoding.encode(message.content))
        return role_tokens + content_tokens
    except ImportError:
        logger.warning("tiktoken not available, using character approximation")
        # tiktokenが利用できない場合は文字数をトークン数の近似値として使用
        # 英語テキストでは約4文字が1トークンに相当
        role_tokens = 4
        content_tokens = len(message.content) // 4
        return role_tokens + content_tokens
    except Exception as e:
        logger.warning(f"Failed to estimate tokens: {str(e)}")
        # 失敗した場合は文字数をトークン数の近似値として使用
        role_tokens = 4
        content_tokens = len(message.content) // 4
        return role_tokens + content_tokens


def estimate_conversation_tokens(
    conversation_history: List[MessageItem], encoding_name: str = "cl100k_base"
) -> int:
    """
    会話履歴全体のトークン数を推定する。

    Args:
        conversation_history: トークン数を推定する会話履歴
        encoding_name: 使用するエンコーディング名

    Returns:
        int: 推定トークン数
    """
    if not conversation_history:
        return 0

    total_tokens = 0
    # 会話のフォーマットのオーバーヘッド（おおよそ）
    overhead_tokens = 3

    for message in conversation_history:
        total_tokens += estimate_message_tokens(message, encoding_name)

    return total_tokens + overhead_tokens


def optimize_conversation_history(
    history: List[MessageItem],
    max_tokens: int = DEFAULT_MAX_TOKENS,
    preserve_recent: int = 2,
    encoding_name: str = "cl100k_base",
) -> Tuple[List[MessageItem], Dict[str, Any]]:
    """
    トークン制限内に収まるよう会話履歴を最適化する。

    会話履歴が指定されたトークン数を超える場合、
    最も古いメッセージから削除していく。
    ただし、指定された数の最新メッセージは常に保持する。

    Args:
        history: 最適化する会話履歴
        max_tokens: 最大トークン数
        preserve_recent: 常に保持する最新メッセージ数
        encoding_name: 使用するエンコーディング名

    Returns:
        Tuple[List[MessageItem], Dict[str, Any]]: 最適化された会話履歴と最適化情報
    """
    if not history:
        return [], {"was_optimized": False, "reason": "Empty history"}

    # 元の履歴のトークン数を計算
    original_tokens = estimate_conversation_tokens(history, encoding_name)

    # 最適化が不要な場合
    if original_tokens <= max_tokens:
        optimization_info = {
            "was_optimized": False,
            "reason": "Within token limit",
            "original_message_count": len(history),
            "optimized_message_count": len(history),
            "original_tokens": original_tokens,
            "optimized_tokens": original_tokens,
        }
        return history.copy(), optimization_info

    # 最新のN個を保存するため、履歴を逆順にする
    preserved_messages = (
        history[-preserve_recent:] if len(history) > preserve_recent else history.copy()
    )
    remaining_messages = (
        history[:-preserve_recent] if len(history) > preserve_recent else []
    )

    # 保存するメッセージのトークン数を計算
    preserved_tokens = estimate_conversation_tokens(preserved_messages, encoding_name)

    # 残りのトークン数
    remaining_token_budget = max_tokens - preserved_tokens

    # トークン数に余裕がある場合は、古いメッセージも可能な限り含める
    optimized_history = []

    # 新しい順に追加していく
    for message in reversed(remaining_messages):
        message_tokens = estimate_message_tokens(message, encoding_name)
        if remaining_token_budget >= message_tokens:
            optimized_history.append(message)
            remaining_token_budget -= message_tokens
        else:
            break

    # 時系列順に戻す
    optimized_history.reverse()

    # 保存するメッセージを追加
    optimized_history.extend(preserved_messages)

    # 最適化情報を作成
    optimized_tokens = estimate_conversation_tokens(optimized_history, encoding_name)
    optimization_info = {
        "was_optimized": True,
        "optimization_method": "truncation",
        "original_message_count": len(history),
        "optimized_message_count": len(optimized_history),
        "original_tokens": original_tokens,
        "optimized_tokens": optimized_tokens,
        "messages_removed": len(history) - len(optimized_history),
    }

    logger.debug(
        f"Optimized conversation history: {len(history)} messages -> {len(optimized_history)} messages, "
        f"tokens: ~{optimized_tokens}/{max_tokens}"
    )

    return optimized_history, optimization_info


def format_conversation_for_provider(
    conversation_history: List[MessageItem], provider: str
) -> List[Dict[str, Any]]:
    """
    会話履歴を特定のプロバイダ形式に変換する。

    Args:
        conversation_history: 変換する会話履歴
        provider: LLMプロバイダ名 ('openai', 'anthropic', 'ollama' など)

    Returns:
        List[Dict[str, Any]]: プロバイダ形式の会話履歴
    """
    if not conversation_history:
        return []

    if provider.lower() == "openai":
        # OpenAI形式: {"role": "user|assistant|system", "content": "..."}
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in conversation_history
        ]

    elif provider.lower() == "anthropic":
        # Anthropic形式: Claude用の形式
        formatted = []
        for msg in conversation_history:
            if msg.role.value == "user":
                formatted.append({"role": "human", "content": msg.content})
            elif msg.role.value == "assistant":
                formatted.append({"role": "assistant", "content": msg.content})
            elif msg.role.value == "system":
                # システムメッセージは最初に一つだけ
                if not formatted or formatted[0].get("role") != "system":
                    formatted.insert(0, {"role": "system", "content": msg.content})
        return formatted

    elif provider.lower() == "ollama":
        # Ollama形式: {"role": "user|assistant|system", "content": "..."}
        # 基本的にOpenAIと同じ
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in conversation_history
        ]

    else:
        # デフォルトはOpenAI形式に準ずる
        logger.warning(f"Unknown provider '{provider}', using OpenAI format as default")
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in conversation_history
        ]


async def summarize_conversation_history(
    history: List[MessageItem],
    llm_service: Any,  # LLMServiceBaseの循環インポートを避けるためAnyを使用
    max_messages_to_keep: int = 6,
    summary_prompt_template: Optional[str] = None,
) -> Tuple[List[MessageItem], Dict[str, Any]]:
    """
    長い会話履歴を要約して、最新のメッセージと要約を組み合わせた最適化済み履歴を返す。

    Args:
        history: 要約する会話履歴
        llm_service: 要約に使用するLLMサービス
        max_messages_to_keep: 要約対象外として保持する最新メッセージ数
        summary_prompt_template: 要約に使用するプロンプトテンプレート

    Returns:
        Tuple[List[MessageItem], Dict[str, Any]]:
            最適化された会話履歴と最適化情報
    """
    if len(history) <= max_messages_to_keep:
        return history, {"optimization_applied": False, "reason": "Below threshold"}

    # システムメッセージを分離
    system_messages = [msg for msg in history if msg.role == MessageRole.SYSTEM]
    conversation_messages = [msg for msg in history if msg.role != MessageRole.SYSTEM]

    if len(conversation_messages) <= max_messages_to_keep:
        return history, {
            "optimization_applied": False,
            "reason": "Below threshold after system separation",
        }

    # 最新のメッセージを保持
    recent_messages = conversation_messages[-max_messages_to_keep:]
    messages_to_summarize = conversation_messages[:-max_messages_to_keep]

    if not messages_to_summarize:
        return history, {
            "optimization_applied": False,
            "reason": "No messages to summarize",
        }

    # 要約用のプロンプトを準備
    if summary_prompt_template is None:
        summary_prompt_template = """以下の会話履歴を簡潔に要約してください。重要な文脈と情報を保持しながら、簡潔にまとめてください。

会話履歴:
{conversation_text}

要約:"""

    # 会話履歴をテキストに変換
    conversation_text = "\n".join(
        [f"{msg.role.value}: {msg.content}" for msg in messages_to_summarize]
    )

    summary_prompt = summary_prompt_template.format(conversation_text=conversation_text)

    try:
        # LLMサービスを使用して要約を生成
        summary_response = await llm_service.query(
            summary_prompt,
            conversation_history=None,  # 要約時は履歴を使用しない
            options={"temperature": 0.3, "max_tokens": 500},  # 要約は一貫性を重視
        )

        # 要約を含む最適化済み履歴を作成
        summary_message = MessageItem(
            role=MessageRole.ASSISTANT,
            content=f"[会話要約] {summary_response.content}",
            timestamp=datetime.now(),
        )

        # システムメッセージ + 要約 + 最新メッセージ
        optimized_history = system_messages + [summary_message] + recent_messages

        optimization_info = {
            "optimization_applied": True,
            "original_message_count": len(history),
            "optimized_message_count": len(optimized_history),
            "summarized_message_count": len(messages_to_summarize),
            "kept_recent_message_count": len(recent_messages),
            "summary_tokens": estimate_message_tokens(summary_message),
        }

        return optimized_history, optimization_info

    except Exception as e:
        logger.error(f"Failed to summarize conversation history: {str(e)}")
        # 要約に失敗した場合は、古いメッセージを削除して最新メッセージのみ保持
        fallback_history = system_messages + recent_messages
        optimization_info = {
            "optimization_applied": True,
            "optimization_method": "fallback_truncation",
            "original_message_count": len(history),
            "optimized_message_count": len(fallback_history),
            "error": str(e),
        }
        return fallback_history, optimization_info


# Function Calling 関連のユーティリティ関数


def validate_function_call_arguments(
    function_call: "FunctionCall", function_definition: "FunctionDefinition"
) -> bool:
    """
    Function callの引数が関数定義に適合するかを検証する。

    Args:
        function_call: LLMからのFunction call
        function_definition: 関数定義

    Returns:
        bool: 引数が有効かどうか
    """
    import json

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


def convert_function_definition_to_openai_tool(
    function_def: "FunctionDefinition",
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


def parse_openai_tool_calls(tool_calls: List[Any]) -> List["ToolCall"]:
    """
    OpenAI APIからのtool callsをToolCallモデルに変換する。

    Args:
        tool_calls: OpenAI APIからのtool calls

    Returns:
        List[ToolCall]: 変換されたToolCallのリスト
    """
    from doc_ai_helper_backend.models.llm import ToolCall, FunctionCall

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
