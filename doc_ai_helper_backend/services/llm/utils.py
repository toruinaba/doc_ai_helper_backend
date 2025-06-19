"""
LLM utility functions.

This module provides utility functions for working with LLM services.
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime

from doc_ai_helper_backend.models.llm import MessageItem, MessageRole

logger = logging.getLogger(__name__)

# デフォルトのトークン限界値（OpenAI GPT-4: 8k）
DEFAULT_MAX_TOKENS = 8000


def estimate_message_tokens(
    message: MessageItem, encoding_name: str = "cl100k_base"
) -> int:
    """
    単一のメッセージのおおよそのトークン数を推定する。

    Args:
        message: トークン数を推定するメッセージ
        encoding_name: 使用するエンコーディング名

    Returns:
        int: 推定トークン数
    """
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
) -> List[MessageItem]:
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
        List[MessageItem]: 最適化された会話履歴
    """
    if not history:
        return []

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

    logger.debug(
        f"Optimized conversation history: {len(history)} messages -> {len(optimized_history)} messages, "
        f"tokens: ~{estimate_conversation_tokens(optimized_history, encoding_name)}/{max_tokens}"
    )

    return optimized_history


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
