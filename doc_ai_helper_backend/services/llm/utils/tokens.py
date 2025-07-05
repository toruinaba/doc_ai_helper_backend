"""
Token estimation utilities for LLM services.

This module provides functions for estimating token counts in texts and conversations.
"""

from typing import Union, List
import logging

from doc_ai_helper_backend.models.llm import MessageItem

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
    if not hasattr(message, "content"):
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


# Alias for backward compatibility
estimate_tokens_for_messages = estimate_conversation_tokens


def optimize_conversation_history(
    conversation_history: List[MessageItem],
    max_tokens: int = DEFAULT_MAX_TOKENS,
    verbose: bool = False,
    preserve_recent: int = 2,
) -> tuple[List[MessageItem], dict]:
    """
    Optimize conversation history to fit within token limits.

    Args:
        conversation_history: List of conversation messages
        max_tokens: Maximum allowed tokens
        verbose: Whether to include optimization details
        preserve_recent: Number of recent messages to preserve

    Returns:
        tuple: (optimized_conversation, optimization_info)
    """
    if not conversation_history:
        return [], {"was_optimized": False, "removed_messages": 0, "tokens_saved": 0}

    # Always return a copy, not the original list
    conversation_copy = conversation_history.copy()

    total_tokens = estimate_conversation_tokens(conversation_copy)

    if total_tokens <= max_tokens:
        return conversation_copy, {
            "was_optimized": False,
            "removed_messages": 0,
            "tokens_saved": 0,
            "original_tokens": total_tokens,
            "optimized_tokens": total_tokens,
        }

    # Start from the most recent messages and work backwards
    optimized = []
    current_tokens = 0
    removed_count = 0

    # Preserve the most recent messages
    recent_messages = (
        conversation_copy[-preserve_recent:] if preserve_recent > 0 else []
    )
    older_messages = (
        conversation_copy[:-preserve_recent]
        if preserve_recent > 0
        else conversation_copy
    )

    # Add recent messages first
    for message in recent_messages:
        message_tokens = estimate_message_tokens(message)
        current_tokens += message_tokens
        optimized.append(message)

    # Add older messages if they fit
    for message in reversed(older_messages):
        message_tokens = estimate_message_tokens(message)
        if current_tokens + message_tokens <= max_tokens:
            optimized.insert(0, message)
            current_tokens += message_tokens
        else:
            removed_count += 1

    tokens_saved = total_tokens - current_tokens

    optimization_info = {
        "was_optimized": True,
        "optimization_method": "truncation",
        "removed_messages": removed_count,
        "tokens_saved": tokens_saved,
        "original_tokens": total_tokens,
        "optimized_tokens": current_tokens,
    }

    if verbose:
        optimization_info["details"] = (
            f"Removed {removed_count} messages, saved {tokens_saved} tokens"
        )

    return optimized, optimization_info
