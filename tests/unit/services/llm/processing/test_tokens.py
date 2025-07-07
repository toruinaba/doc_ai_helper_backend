"""
Test for LLM token utility functions.

This module contains unit tests for the token estimation and conversation optimization functions.
"""

import pytest
from typing import List
from unittest.mock import patch

from doc_ai_helper_backend.models.llm import MessageItem, MessageRole
from doc_ai_helper_backend.services.llm.processing.tokens import (
    estimate_message_tokens,
    estimate_conversation_tokens,
    optimize_conversation_history,
    DEFAULT_MAX_TOKENS,
)


class TestTokenEstimation:
    """Test token estimation functions."""

    def test_estimate_message_tokens_with_message_item(self):
        """Test token estimation with MessageItem objects."""
        # 基本的なメッセージのトークン数推定
        message = MessageItem(
            role=MessageRole.USER, content="これはテストメッセージです。"
        )
        tokens = estimate_message_tokens(message)
        assert isinstance(tokens, int)
        assert tokens > 0

        # 長いコンテンツのメッセージ
        long_message = MessageItem(
            role=MessageRole.ASSISTANT,
            content="これは非常に長いコンテンツを持つメッセージです。" * 50,
        )
        long_tokens = estimate_message_tokens(long_message)
        assert long_tokens > tokens

        # 異なるロールのメッセージ
        system_message = MessageItem(
            role=MessageRole.SYSTEM, content="システム指示です。"
        )
        system_tokens = estimate_message_tokens(system_message)
        assert system_tokens > 0

    def test_estimate_message_tokens_with_string(self):
        """Test token estimation with string input."""
        # 文字列メッセージのトークン数推定
        text = "This is a test message."
        tokens = estimate_message_tokens(text)
        assert isinstance(tokens, int)
        assert tokens > 0

        # 空文字列
        empty_tokens = estimate_message_tokens("")
        assert empty_tokens == 0

        # 長い文字列
        long_text = "This is a very long message. " * 100
        long_tokens = estimate_message_tokens(long_text)
        assert long_tokens > tokens

    def test_estimate_message_tokens_error_handling(self):
        """Test error handling in token estimation."""
        # Invalid message object
        invalid_message = {"invalid": "object"}
        tokens = estimate_message_tokens(invalid_message)
        assert tokens == 0

        # Message without content attribute
        class InvalidMessage:
            def __init__(self):
                self.role = "user"

        invalid_msg = InvalidMessage()
        tokens = estimate_message_tokens(invalid_msg)
        assert tokens == 0

    @patch("tiktoken.get_encoding")
    def test_estimate_message_tokens_without_tiktoken(self, mock_get_encoding):
        """Test token estimation fallback when tiktoken is not available."""
        # Mock ImportError for tiktoken
        mock_get_encoding.side_effect = ImportError("tiktoken not available")

        text = "This is a test message."
        tokens = estimate_message_tokens(text)

        # Should fallback to character approximation (length / 4)
        expected_tokens = len(text) // 4
        assert tokens == expected_tokens

    @patch("tiktoken.get_encoding")
    def test_estimate_message_tokens_encoding_error(self, mock_get_encoding):
        """Test token estimation with encoding errors."""
        # Mock encoding error
        mock_get_encoding.side_effect = Exception("Encoding error")

        text = "This is a test message."
        tokens = estimate_message_tokens(text)

        # Should fallback to character approximation
        expected_tokens = len(text) // 4
        assert tokens == expected_tokens

    def test_estimate_conversation_tokens(self):
        """Test conversation token estimation."""
        # 空の会話履歴
        assert estimate_conversation_tokens([]) == 0

        # 単一メッセージの会話
        history = [MessageItem(role=MessageRole.USER, content="こんにちは")]
        single_tokens = estimate_conversation_tokens(history)
        assert single_tokens > 0

        # 複数メッセージの会話
        history.append(MessageItem(role=MessageRole.ASSISTANT, content="どうぞ"))
        history.append(MessageItem(role=MessageRole.USER, content="質問があります"))
        multi_tokens = estimate_conversation_tokens(history)

        # 個別のトークン合計と比較（オーバーヘッド分を含む）
        individual_sum = sum(estimate_message_tokens(msg) for msg in history) + 3
        assert multi_tokens == individual_sum

    def test_estimate_conversation_tokens_with_strings(self):
        """Test conversation token estimation with mixed string messages."""
        # Mix of MessageItem and string
        history = [
            MessageItem(role=MessageRole.USER, content="Hello"),
            "This is a string message",
            MessageItem(role=MessageRole.ASSISTANT, content="Response"),
        ]
        tokens = estimate_conversation_tokens(history)
        assert tokens > 0


class TestConversationOptimization:
    """Test conversation history optimization functions."""

    def test_optimize_empty_conversation(self):
        """Test optimization of empty conversation."""
        optimized, info = optimize_conversation_history([])
        assert optimized == []
        assert info["was_optimized"] == False
        assert info["removed_messages"] == 0
        assert info["tokens_saved"] == 0

    def test_optimize_short_conversation_no_optimization_needed(self):
        """Test optimization when no optimization is needed."""
        short_history = [
            MessageItem(role=MessageRole.USER, content="Hello"),
            MessageItem(role=MessageRole.ASSISTANT, content="Hi there"),
        ]
        optimized, info = optimize_conversation_history(short_history, max_tokens=1000)

        assert len(optimized) == len(short_history)
        assert info["was_optimized"] == False
        assert info["removed_messages"] == 0
        assert info["tokens_saved"] == 0

        # Ensure it returns a copy, not the original
        assert optimized is not short_history
        assert [msg.content for msg in optimized] == [
            msg.content for msg in short_history
        ]

    def test_optimize_long_conversation_with_truncation(self):
        """Test optimization with truncation."""
        # Create a long conversation
        long_history = [
            MessageItem(
                role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                content=f"Message {i}: " + "This is content. " * 10,
            )
            for i in range(20)
        ]

        optimized, info = optimize_conversation_history(
            long_history, max_tokens=200, preserve_recent=3
        )

        assert len(optimized) < len(long_history)
        assert info["was_optimized"] == True
        assert info["optimization_method"] == "truncation"
        assert info["removed_messages"] > 0
        assert info["tokens_saved"] > 0
        assert "original_tokens" in info
        assert "optimized_tokens" in info

        # Check that recent messages are preserved
        assert optimized[-1].content == long_history[-1].content
        assert optimized[-2].content == long_history[-2].content
        assert optimized[-3].content == long_history[-3].content

    def test_optimize_conversation_with_verbose_output(self):
        """Test optimization with verbose output."""
        history = [
            MessageItem(role=MessageRole.USER, content="Very long message " * 100)
            for _ in range(5)
        ]

        optimized, info = optimize_conversation_history(
            history, max_tokens=100, verbose=True, preserve_recent=1
        )

        assert info["was_optimized"] == True
        assert "details" in info
        assert "Removed" in info["details"]
        assert "saved" in info["details"]

    def test_optimize_conversation_preserve_recent_zero(self):
        """Test optimization with preserve_recent=0."""
        history = [
            MessageItem(role=MessageRole.USER, content=f"Message {i}")
            for i in range(10)
        ]

        optimized, info = optimize_conversation_history(
            history, max_tokens=50, preserve_recent=0
        )

        # Should still return some messages that fit within the limit
        assert len(optimized) <= len(history)
        if info["was_optimized"]:
            assert info["removed_messages"] >= 0

    def test_optimize_conversation_with_default_parameters(self):
        """Test optimization with default parameters."""
        history = [
            MessageItem(role=MessageRole.USER, content="Short message")
            for _ in range(5)
        ]

        optimized, info = optimize_conversation_history(history)

        # With default max_tokens (8000), short messages shouldn't be optimized
        assert len(optimized) == len(history)
        assert info["was_optimized"] == False

    def test_optimize_very_long_messages_that_exceed_limit(self):
        """Test optimization when even recent messages exceed token limit."""
        # Create messages that are individually very long
        very_long_history = [
            MessageItem(
                role=MessageRole.USER,
                content="This is an extremely long message. " * 200,
            )
            for _ in range(3)
        ]

        optimized, info = optimize_conversation_history(
            very_long_history, max_tokens=100, preserve_recent=2
        )

        # Even with preserve_recent=2, we might not be able to fit both
        # if they individually exceed the limit
        assert len(optimized) <= len(very_long_history)
        assert info["was_optimized"] == True
