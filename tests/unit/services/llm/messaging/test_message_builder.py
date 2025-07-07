"""
Tests for message builder utilities.
"""

import pytest
from datetime import datetime
from doc_ai_helper_backend.models.llm import MessageItem, MessageRole
from doc_ai_helper_backend.services.llm.messaging.message_builder import MessageBuilder


class TestMessageBuilder:
    """Test the MessageBuilder class."""

    def test_create_system_message(self):
        """Test creating a system message."""
        content = "You are a helpful assistant."
        message = MessageBuilder.create_system_message(content)

        assert message.role == MessageRole.SYSTEM
        assert message.content == content
        assert isinstance(message.timestamp, datetime)

    def test_create_user_message(self):
        """Test creating a user message."""
        content = "Hello, how are you?"
        message = MessageBuilder.create_user_message(content)

        assert message.role == MessageRole.USER
        assert message.content == content
        assert isinstance(message.timestamp, datetime)

    def test_create_assistant_message(self):
        """Test creating an assistant message."""
        content = "I'm doing well, thank you!"
        message = MessageBuilder.create_assistant_message(content)

        assert message.role == MessageRole.ASSISTANT
        assert message.content == content
        assert isinstance(message.timestamp, datetime)

    def test_format_messages_for_api(self):
        """Test formatting messages for API."""
        messages = [
            MessageBuilder.create_system_message("System prompt"),
            MessageBuilder.create_user_message("User input"),
            MessageBuilder.create_assistant_message("Assistant response"),
        ]

        formatted = MessageBuilder.format_messages_for_api(messages)

        assert len(formatted) == 3
        assert formatted[0]["role"] == "system"
        assert formatted[0]["content"] == "System prompt"
        assert formatted[1]["role"] == "user"
        assert formatted[1]["content"] == "User input"
        assert formatted[2]["role"] == "assistant"
        assert formatted[2]["content"] == "Assistant response"

    def test_format_empty_messages(self):
        """Test formatting empty message list."""
        formatted = MessageBuilder.format_messages_for_api([])
        assert formatted == []
