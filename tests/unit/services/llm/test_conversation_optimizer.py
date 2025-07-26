"""
Test suite for Conversation Optimizer

会話履歴最適化機能のテストスイート
"""

import pytest
from unittest.mock import patch
from typing import List

from doc_ai_helper_backend.services.llm.conversation_optimizer import (
    estimate_message_tokens,
    optimize_conversation_history,
    build_conversation_messages,
)
from doc_ai_helper_backend.models.llm import MessageItem, MessageRole


class TestConversationHistoryOptimization:
    """Test conversation history optimization functions."""

    def test_estimate_message_tokens_basic(self):
        """Test basic token estimation."""
        message = MessageItem(role=MessageRole.USER, content="Hello world")
        tokens = estimate_message_tokens(message)
        assert isinstance(tokens, int)
        assert tokens > 0

    def test_estimate_message_tokens_long_content(self):
        """Test token estimation with long content."""
        long_content = "This is a very long message " * 20
        message = MessageItem(role=MessageRole.USER, content=long_content)
        tokens = estimate_message_tokens(message)
        assert isinstance(tokens, int)
        assert tokens > 50  # Should be significantly more than short message

    def test_estimate_message_tokens_fallback(self):
        """Test token estimation fallback when tiktoken is not available."""
        # Mock tiktoken import to raise ImportError
        with patch.dict('sys.modules', {'tiktoken': None}):
            # Reload the function to trigger ImportError path
            import importlib
            import doc_ai_helper_backend.services.llm.conversation_optimizer as conv_module
            importlib.reload(conv_module)
            
            message = MessageItem(role=MessageRole.USER, content="Test message for fallback")
            tokens = conv_module.estimate_message_tokens(message)
            
            # Should fall back to character/4 approximation
            assert isinstance(tokens, int)
            assert tokens > 0
            # Should be approximately len(content) // 4 plus role text
            assert tokens >= 5  # At least some tokens for the message

    def test_optimize_conversation_history_basic(self):
        """Test conversation history optimization."""
        history = [
            MessageItem(role=MessageRole.USER, content="Question 1"),
            MessageItem(role=MessageRole.ASSISTANT, content="Answer 1"),
            MessageItem(role=MessageRole.USER, content="Question 2"),
            MessageItem(role=MessageRole.ASSISTANT, content="Answer 2"),
        ]
        
        optimized, info = optimize_conversation_history(history, max_tokens=1000)
        
        assert isinstance(optimized, list)
        assert isinstance(info, dict)
        assert "was_optimized" in info
        assert "original_messages" in info
        assert "final_messages" in info

    def test_optimize_conversation_history_empty(self):
        """Test optimization with empty history."""
        optimized, info = optimize_conversation_history([], max_tokens=1000)
        
        assert optimized == []
        assert info["was_optimized"] is False
        assert "original_messages" not in info  # Empty history doesn't have these keys
        assert "final_messages" not in info

    def test_optimize_conversation_history_large(self):
        """Test optimization with large history that needs truncation."""
        # Create a large history that should trigger optimization
        large_history = []
        for i in range(50):
            large_history.extend([
                MessageItem(role=MessageRole.USER, content=f"Long question {i} " * 20),
                MessageItem(role=MessageRole.ASSISTANT, content=f"Long answer {i} " * 20),
            ])
        
        optimized, info = optimize_conversation_history(large_history, max_tokens=500)
        
        assert len(optimized) <= len(large_history)
        assert info["was_optimized"] is True
        assert info["final_messages"] < info["original_messages"]

    def test_optimize_conversation_history_preserve_recent(self):
        """Test that recent messages are preserved during optimization."""
        history = []
        for i in range(20):
            history.extend([
                MessageItem(role=MessageRole.USER, content=f"Question {i} " * 10),
                MessageItem(role=MessageRole.ASSISTANT, content=f"Answer {i} " * 10),
            ])
        
        preserve_recent = 4
        optimized, info = optimize_conversation_history(
            history, max_tokens=200, preserve_recent=preserve_recent
        )
        
        # Should always preserve at least the recent messages
        assert len(optimized) >= preserve_recent
        # The last preserve_recent messages should be identical
        assert optimized[-preserve_recent:] == history[-preserve_recent:]

    def test_optimize_conversation_history_within_limit(self):
        """Test optimization when history is already within token limit."""
        small_history = [
            MessageItem(role=MessageRole.USER, content="Hi"),
            MessageItem(role=MessageRole.ASSISTANT, content="Hello"),
        ]
        
        optimized, info = optimize_conversation_history(small_history, max_tokens=1000)
        
        assert optimized == small_history
        assert info["was_optimized"] is False
        assert info["reason"] == "History within token limit"


class TestBuildConversationMessages:
    """Test conversation message building functionality."""

    def test_build_conversation_messages_basic(self):
        """Test basic message building."""
        prompt = "What is the weather today?"
        messages = build_conversation_messages(prompt)
        
        assert len(messages) == 1
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == prompt

    def test_build_conversation_messages_with_system_prompt(self):
        """Test message building with system prompt."""
        prompt = "What is the weather today?"
        system_prompt = "You are a helpful weather assistant."
        
        messages = build_conversation_messages(prompt, system_prompt=system_prompt)
        
        assert len(messages) == 2
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[0].content == system_prompt
        assert messages[1].role == MessageRole.USER
        assert messages[1].content == prompt

    def test_build_conversation_messages_with_history(self):
        """Test message building with conversation history."""
        prompt = "What about tomorrow?"
        history = [
            MessageItem(role=MessageRole.USER, content="What is the weather today?"),
            MessageItem(role=MessageRole.ASSISTANT, content="It's sunny today."),
        ]
        
        messages = build_conversation_messages(prompt, conversation_history=history)
        
        assert len(messages) == 3
        assert messages[0] == history[0]
        assert messages[1] == history[1]
        assert messages[2].role == MessageRole.USER
        assert messages[2].content == prompt

    def test_build_conversation_messages_complete(self):
        """Test message building with all parameters."""
        prompt = "What about tomorrow?"
        system_prompt = "You are a weather assistant."
        history = [
            MessageItem(role=MessageRole.USER, content="What is the weather today?"),
            MessageItem(role=MessageRole.ASSISTANT, content="It's sunny today."),
        ]
        
        messages = build_conversation_messages(
            prompt, conversation_history=history, system_prompt=system_prompt
        )
        
        assert len(messages) == 4
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[0].content == system_prompt
        assert messages[1] == history[0]
        assert messages[2] == history[1]
        assert messages[3].role == MessageRole.USER
        assert messages[3].content == prompt

    def test_build_conversation_messages_empty_history(self):
        """Test message building with empty history."""
        prompt = "Hello"
        messages = build_conversation_messages(prompt, conversation_history=[])
        
        assert len(messages) == 1
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == prompt