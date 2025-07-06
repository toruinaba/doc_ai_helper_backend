"""
Test for LLM messaging utility functions.

This module contains unit tests for the message formatting and conversation handling functions.
"""

import pytest
from typing import List
import asyncio
from unittest.mock import AsyncMock
from datetime import datetime

from doc_ai_helper_backend.models.llm import (
    MessageItem,
    MessageRole,
    LLMResponse,
    LLMUsage,
)
from doc_ai_helper_backend.services.llm.components.messaging import (
    format_conversation_for_provider,
    summarize_conversation_history,
)


def test_format_conversation_for_provider():
    """プロバイダー形式変換機能のテスト"""
    # テスト用の会話履歴
    history = [
        MessageItem(role=MessageRole.SYSTEM, content="システム指示"),
        MessageItem(role=MessageRole.USER, content="ユーザーの質問"),
        MessageItem(role=MessageRole.ASSISTANT, content="アシスタントの回答"),
    ]

    # OpenAI形式への変換
    openai_format = format_conversation_for_provider(history, "openai")
    assert isinstance(openai_format, list)
    assert len(openai_format) == 3
    assert openai_format[0]["role"] == "system"
    assert openai_format[0]["content"] == "システム指示"
    assert openai_format[1]["role"] == "user"
    assert openai_format[1]["content"] == "ユーザーの質問"
    assert openai_format[2]["role"] == "assistant"
    assert openai_format[2]["content"] == "アシスタントの回答"

    # Anthropic形式への変換
    anthropic_format = format_conversation_for_provider(history, "anthropic")
    assert isinstance(anthropic_format, list)
    assert anthropic_format[0]["role"] == "system"
    assert anthropic_format[1]["role"] == "human"  # userではなくhuman
    assert anthropic_format[2]["role"] == "assistant"

    # Ollama形式への変換
    ollama_format = format_conversation_for_provider(history, "ollama")
    assert isinstance(ollama_format, list)
    assert ollama_format[0]["role"] == "system"
    assert ollama_format[1]["role"] == "user"
    assert ollama_format[2]["role"] == "assistant"

    # 未知のプロバイダー（デフォルトでOpenAI形式）
    unknown_format = format_conversation_for_provider(history, "unknown")
    assert unknown_format[0]["role"] == "system"
    assert unknown_format[1]["role"] == "user"
    assert unknown_format[2]["role"] == "assistant"


def test_format_conversation_edge_cases():
    """変換のエッジケースをテスト"""
    # 空の会話履歴
    empty_history = []
    assert format_conversation_for_provider(empty_history, "openai") == []

    # システムメッセージが複数ある場合（Anthropic）
    multiple_system = [
        MessageItem(role=MessageRole.SYSTEM, content="システム指示1"),
        MessageItem(role=MessageRole.SYSTEM, content="システム指示2"),
        MessageItem(role=MessageRole.USER, content="質問"),
    ]

    anthropic_format = format_conversation_for_provider(multiple_system, "anthropic")
    # Anthropicは最初のシステムメッセージのみ利用するはず
    system_messages = [msg for msg in anthropic_format if msg["role"] == "system"]
    assert len(system_messages) == 1


def test_format_conversation_role_mapping():
    """ロールマッピングの詳細テスト"""
    # 全てのロールタイプをテスト
    all_roles_history = [
        MessageItem(role=MessageRole.SYSTEM, content="システム"),
        MessageItem(role=MessageRole.USER, content="ユーザー"),
        MessageItem(role=MessageRole.ASSISTANT, content="アシスタント"),
    ]

    # OpenAI: 全てそのまま
    openai_result = format_conversation_for_provider(all_roles_history, "openai")
    expected_openai_roles = ["system", "user", "assistant"]
    actual_openai_roles = [msg["role"] for msg in openai_result]
    assert actual_openai_roles == expected_openai_roles

    # Anthropic: user -> human
    anthropic_result = format_conversation_for_provider(all_roles_history, "anthropic")
    expected_anthropic_roles = ["system", "human", "assistant"]
    actual_anthropic_roles = [msg["role"] for msg in anthropic_result]
    assert actual_anthropic_roles == expected_anthropic_roles


# === Conversation Summarization Tests ===
# Tests moved from test_conversation_summarization.py for better organization


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
