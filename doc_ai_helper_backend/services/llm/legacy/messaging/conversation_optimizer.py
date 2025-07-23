"""
Conversation Optimizer (Conversation Optimizer)

LLMサービス向けの会話履歴最適化機能を提供します。

主要機能:
- トークン制限に基づく会話履歴の最適化
- LLMを使用した会話履歴の要約
- 最適化情報の提供
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from doc_ai_helper_backend.models.llm import MessageItem, MessageRole

logger = logging.getLogger(__name__)

# デフォルトの最大トークン数
DEFAULT_MAX_TOKENS = 4000


def estimate_message_tokens(
    message: MessageItem, encoding_name: str = "cl100k_base"
) -> int:
    """
    単一メッセージのトークン数を推定する

    Args:
        message: トークン数を推定するメッセージ
        encoding_name: 使用するエンコーディング名

    Returns:
        int: 推定トークン数
    """
    try:
        import tiktoken

        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(f"{message.role.value}: {message.content}"))
    except ImportError:
        # tiktokenが利用できない場合は単純な推定
        return len(message.content) // 4  # 4文字 ≈ 1トークンの概算


def estimate_conversation_tokens(
    history: List[MessageItem], encoding_name: str = "cl100k_base"
) -> int:
    """
    会話履歴全体のトークン数を推定する

    Args:
        history: トークン数を推定する会話履歴
        encoding_name: 使用するエンコーディング名

    Returns:
        int: 推定トークン数
    """
    return sum(estimate_message_tokens(msg, encoding_name) for msg in history)


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

    # 最適化情報
    optimized_tokens = estimate_conversation_tokens(optimized_history, encoding_name)
    optimization_info = {
        "was_optimized": True,
        "reason": "Token limit exceeded",
        "original_message_count": len(history),
        "optimized_message_count": len(optimized_history),
        "original_tokens": original_tokens,
        "optimized_tokens": optimized_tokens,
        "messages_removed": len(history) - len(optimized_history),
        "messages_preserved": preserve_recent,
    }

    return optimized_history, optimization_info


async def optimize_conversation_with_summary(
    history: List[MessageItem],
    llm_service,  # LLMServiceBaseのインスタンス
    max_messages_to_keep: int = 10,
    summary_prompt_template: Optional[str] = None,
) -> Tuple[List[MessageItem], Dict[str, Any]]:
    """
    LLMを使用して会話履歴を要約し、最適化する。

    古い会話を要約して1つのメッセージにまとめ、
    最新のメッセージと組み合わせて効率的なコンテキストを作成する。

    Args:
        history: 最適化する会話履歴
        llm_service: 要約に使用するLLMサービス
        max_messages_to_keep: 要約せずに保持する最新メッセージ数
        summary_prompt_template: 要約用のプロンプトテンプレート

    Returns:
        Tuple[List[MessageItem], Dict[str, Any]]: 最適化された会話履歴と最適化情報
    """
    if not history:
        return [], {"optimization_applied": False, "reason": "Empty history"}

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
