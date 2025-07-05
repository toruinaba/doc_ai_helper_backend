"""
Test for LLM messaging utility functions.

This module contains unit tests for the message formatting and conversation handling functions.
"""

import pytest
from typing import List

from doc_ai_helper_backend.models.llm import MessageItem, MessageRole
from doc_ai_helper_backend.services.llm.utils.messaging import (
    format_conversation_for_provider,
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
