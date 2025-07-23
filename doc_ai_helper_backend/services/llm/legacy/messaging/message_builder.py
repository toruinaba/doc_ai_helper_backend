"""
Message Builder (Message Builder)

LLMサービス向けのメッセージ構築とフォーマット機能を提供します。

主要機能:
- メッセージの作成
- API用フォーマットへの変換
"""

from datetime import datetime
from typing import Dict, List

from doc_ai_helper_backend.models.llm import MessageItem, MessageRole


class MessageBuilder:
    """
    メッセージ構築とフォーマットのユーティリティクラス
    """

    @staticmethod
    def create_system_message(content: str) -> MessageItem:
        """システムメッセージを作成"""
        return MessageItem(
            role=MessageRole.SYSTEM, content=content, timestamp=datetime.now()
        )

    @staticmethod
    def create_user_message(content: str) -> MessageItem:
        """ユーザーメッセージを作成"""
        return MessageItem(
            role=MessageRole.USER, content=content, timestamp=datetime.now()
        )

    @staticmethod
    def create_assistant_message(content: str) -> MessageItem:
        """アシスタントメッセージを作成"""
        return MessageItem(
            role=MessageRole.ASSISTANT, content=content, timestamp=datetime.now()
        )

    @staticmethod
    def format_messages_for_api(messages: List[MessageItem]) -> List[Dict[str, str]]:
        """メッセージをAPI用のフォーマットに変換"""
        return [{"role": msg.role.value, "content": msg.content} for msg in messages]
