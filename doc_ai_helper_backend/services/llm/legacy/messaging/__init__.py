"""
Messaging パッケージ - メッセージング機能

分割された各モジュールからの統一エクスポート：
- message_builder: MessageBuilder クラス
- conversation_optimizer: 会話最適化関数群
- conversation_formatter: 会話フォーマット関数群
- prompt_manager: SystemPromptCache, SystemPromptBuilder クラス
"""

from .message_builder import MessageBuilder
from .conversation_optimizer import (
    optimize_conversation_history,
    optimize_conversation_with_summary,
    estimate_message_tokens,
    estimate_conversation_tokens,
)
from .conversation_formatter import (
    format_conversation_for_provider,
    summarize_conversation_history,
)
from .prompt_manager import SystemPromptCache, SystemPromptBuilder

__all__ = [
    "MessageBuilder",
    "optimize_conversation_history",
    "optimize_conversation_with_summary",
    "estimate_message_tokens",
    "estimate_conversation_tokens",
    "format_conversation_for_provider",
    "summarize_conversation_history",
    "SystemPromptCache",
    "SystemPromptBuilder",
]
