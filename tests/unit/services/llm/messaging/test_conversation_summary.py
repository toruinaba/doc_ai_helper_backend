"""
Tests for conversation summary and formatting utilities.
"""

import pytest
from typing import List
from unittest.mock import AsyncMock
from datetime import datetime

from doc_ai_helper_backend.models.llm import (
    MessageItem,
    MessageRole,
    LLMResponse,
    LLMUsage,
)
from doc_ai_helper_backend.services.llm.messaging.conversation_formatter import (
    summarize_conversation_history,
)


class TestConversationSummarization:
    """会話履歴要約機能のテスト"""

    def create_test_conversation(self, num_messages: int = 12) -> List[MessageItem]:
        """テスト用の会話履歴を作成"""
        messages = []

        # システムメッセージ
        messages.append(
            MessageItem(
                role=MessageRole.SYSTEM,
                content="あなたは親切なアシスタントです。",
                timestamp=datetime.now(),
            )
        )

        # 交互にユーザーとアシスタントのメッセージを作成
        for i in range(1, num_messages):
            if i % 2 == 1:  # 奇数: ユーザーメッセージ
                messages.append(
                    MessageItem(
                        role=MessageRole.USER,
                        content=f"これはユーザーの質問 {i} です。",
                        timestamp=datetime.now(),
                    )
                )
            else:  # 偶数: アシスタントメッセージ
                messages.append(
                    MessageItem(
                        role=MessageRole.ASSISTANT,
                        content=f"これはアシスタントの回答 {i} です。",
                        timestamp=datetime.now(),
                    )
                )

        return messages

    @pytest.mark.asyncio
    async def test_summarize_short_conversation(self):
        """短い会話履歴（要約不要）のテスト"""
        # Arrange
        mock_llm_service = AsyncMock()
        short_history = self.create_test_conversation(4)  # 4メッセージ

        # Act
        result_history, optimization_info = await summarize_conversation_history(
            short_history, mock_llm_service, max_messages_to_keep=6
        )

        # Assert
        assert result_history == short_history
        assert optimization_info["optimization_applied"] is False
        assert optimization_info["reason"] == "Below threshold"
        mock_llm_service.query.assert_not_called()

    @pytest.mark.asyncio
    async def test_summarize_long_conversation(self):
        """長い会話履歴（要約が必要）のテスト"""
        # Arrange
        mock_llm_service = AsyncMock()
        mock_llm_service.query.return_value = LLMResponse(
            content="これまでの会話では、ユーザーが様々な質問をし、アシスタントが親切に回答しました。",
            model="gpt-4",
            provider="openai",
            usage=LLMUsage(),
        )

        long_history = self.create_test_conversation(15)  # 15メッセージ

        # Act
        result_history, optimization_info = await summarize_conversation_history(
            long_history, mock_llm_service, max_messages_to_keep=6
        )

        # Assert
        assert len(result_history) < len(long_history)
        assert optimization_info["optimization_applied"] is True
        assert optimization_info["original_message_count"] == 15
        assert optimization_info["kept_recent_message_count"] == 6

        # システムメッセージが保持されていることを確認
        system_messages = [
            msg for msg in result_history if msg.role == MessageRole.SYSTEM
        ]
        assert len(system_messages) >= 1

    @pytest.mark.asyncio
    async def test_summarize_with_custom_threshold(self):
        """カスタム閾値での要約テスト"""
        # Arrange
        mock_llm_service = AsyncMock()
        mock_llm_service.query.return_value = LLMResponse(
            content="要約されたコンテンツ",
            model="gpt-4",
            provider="openai",
            usage=LLMUsage(),
        )

        history = self.create_test_conversation(10)

        # Act
        result_history, optimization_info = await summarize_conversation_history(
            history, mock_llm_service, max_messages_to_keep=3
        )

        # Assert
        assert optimization_info["optimization_applied"] is True
        assert optimization_info["kept_recent_message_count"] == 3
