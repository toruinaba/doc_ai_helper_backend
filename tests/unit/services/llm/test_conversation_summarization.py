"""
Unit tests for conversation history summarization functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from doc_ai_helper_backend.models.llm import MessageItem, MessageRole, LLMResponse, LLMUsage
from doc_ai_helper_backend.services.llm.utils import summarize_conversation_history


class TestConversationSummarization:
    """会話履歴要約機能のテスト"""

    def create_test_conversation(self, num_messages: int = 12) -> list[MessageItem]:
        """テスト用の会話履歴を作成"""
        messages = []
        
        # システムメッセージ
        messages.append(MessageItem(
            role=MessageRole.SYSTEM,
            content="あなたは親切なアシスタントです。",
            timestamp=datetime.now()
        ))
        
        # 交互にユーザーとアシスタントのメッセージを作成
        for i in range(1, num_messages):
            if i % 2 == 1:  # 奇数: ユーザーメッセージ
                messages.append(MessageItem(
                    role=MessageRole.USER,
                    content=f"これはユーザーの質問 {i} です。",
                    timestamp=datetime.now()
                ))
            else:  # 偶数: アシスタントメッセージ
                messages.append(MessageItem(
                    role=MessageRole.ASSISTANT,
                    content=f"これはアシスタントの回答 {i} です。",
                    timestamp=datetime.now()
                ))
        
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
            usage=LLMUsage()
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
        system_messages = [msg for msg in result_history if msg.role == MessageRole.SYSTEM]
        assert len(system_messages) == 1
        assert system_messages[0].content == "あなたは親切なアシスタントです。"
        
        # 要約メッセージが含まれていることを確認
        summary_messages = [msg for msg in result_history if "[会話要約]" in msg.content]
        assert len(summary_messages) == 1
        
        # 最新のメッセージが保持されていることを確認
        last_original_messages = long_history[-6:]
        for i, msg in enumerate(last_original_messages):
            # 要約後の履歴の最後6件と比較（システムメッセージと要約を除く）
            result_without_system_summary = [
                msg for msg in result_history 
                if msg.role != MessageRole.SYSTEM and "[会話要約]" not in msg.content
            ]
            assert result_without_system_summary[i].content == msg.content
        
        # LLMサービスが要約のために呼び出されたことを確認
        mock_llm_service.query.assert_called_once()
        call_args = mock_llm_service.query.call_args
        assert "要約" in call_args[0][0]  # プロンプトに「要約」が含まれている

    @pytest.mark.asyncio
    async def test_summarize_conversation_system_messages_preservation(self):
        """システムメッセージが適切に保持されるかのテスト"""
        # Arrange
        mock_llm_service = AsyncMock()
        mock_llm_service.query.return_value = LLMResponse(
            content="会話要約です",
            model="gpt-4",
            provider="openai",
            usage=LLMUsage()
        )
        
        # 複数のシステムメッセージを含む履歴
        history = [
            MessageItem(role=MessageRole.SYSTEM, content="システム指示1"),
            MessageItem(role=MessageRole.SYSTEM, content="システム指示2"),
            MessageItem(role=MessageRole.USER, content="質問1"),
            MessageItem(role=MessageRole.ASSISTANT, content="回答1"),
            MessageItem(role=MessageRole.USER, content="質問2"),
            MessageItem(role=MessageRole.ASSISTANT, content="回答2"),
            MessageItem(role=MessageRole.USER, content="質問3"),
            MessageItem(role=MessageRole.ASSISTANT, content="回答3"),
            MessageItem(role=MessageRole.USER, content="質問4"),
            MessageItem(role=MessageRole.ASSISTANT, content="回答4"),
        ]
        
        # Act
        result_history, optimization_info = await summarize_conversation_history(
            history, mock_llm_service, max_messages_to_keep=4
        )
        
        # Assert
        system_messages = [msg for msg in result_history if msg.role == MessageRole.SYSTEM]
        assert len(system_messages) == 2
        assert system_messages[0].content == "システム指示1"
        assert system_messages[1].content == "システム指示2"

    @pytest.mark.asyncio
    async def test_summarize_conversation_llm_error_fallback(self):
        """LLM要約が失敗した場合のフォールバック処理のテスト"""
        # Arrange
        mock_llm_service = AsyncMock()
        mock_llm_service.query.side_effect = Exception("LLM API error")
        
        long_history = self.create_test_conversation(12)
        
        # Act
        result_history, optimization_info = await summarize_conversation_history(
            long_history, mock_llm_service, max_messages_to_keep=4
        )
        
        # Assert
        assert len(result_history) < len(long_history)
        assert optimization_info["optimization_applied"] is True
        assert optimization_info["optimization_method"] == "fallback_truncation"
        assert "error" in optimization_info
        
        # システムメッセージ + 最新4件が保持されていることを確認
        system_messages = [msg for msg in result_history if msg.role == MessageRole.SYSTEM]
        non_system_messages = [msg for msg in result_history if msg.role != MessageRole.SYSTEM]
        assert len(system_messages) == 1
        assert len(non_system_messages) == 4

    @pytest.mark.asyncio
    async def test_custom_summary_prompt_template(self):
        """カスタム要約プロンプトテンプレートのテスト"""
        # Arrange
        mock_llm_service = AsyncMock()
        mock_llm_service.query.return_value = LLMResponse(
            content="カスタム要約結果",
            model="gpt-4",
            provider="openai",
            usage=LLMUsage()
        )
        
        long_history = self.create_test_conversation(10)
        custom_template = "次の会話を短くまとめて:\n{conversation_text}\n\n要約:"
        
        # Act
        result_history, optimization_info = await summarize_conversation_history(
            long_history, 
            mock_llm_service, 
            max_messages_to_keep=4,
            summary_prompt_template=custom_template
        )
        
        # Assert
        mock_llm_service.query.assert_called_once()
        call_args = mock_llm_service.query.call_args
        assert "次の会話を短くまとめて:" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_summarize_only_system_messages(self):
        """システムメッセージのみの履歴のテスト"""
        # Arrange
        mock_llm_service = AsyncMock()
        system_only_history = [
            MessageItem(role=MessageRole.SYSTEM, content="システム指示1"),
            MessageItem(role=MessageRole.SYSTEM, content="システム指示2"),
        ]
        
        # Act
        result_history, optimization_info = await summarize_conversation_history(
            system_only_history, mock_llm_service, max_messages_to_keep=6
        )
        
        # Assert
        assert result_history == system_only_history
        assert optimization_info["optimization_applied"] is False
        assert optimization_info["reason"] == "Below threshold"
        mock_llm_service.query.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_conversation_history(self):
        """空の会話履歴のテスト"""
        # Arrange
        mock_llm_service = AsyncMock()
        empty_history = []
        
        # Act
        result_history, optimization_info = await summarize_conversation_history(
            empty_history, mock_llm_service
        )
        
        # Assert
        assert result_history == []
        assert optimization_info["optimization_applied"] is False
        assert optimization_info["reason"] == "Below threshold"
        mock_llm_service.query.assert_not_called()
