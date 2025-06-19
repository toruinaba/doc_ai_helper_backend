"""
Test for LLM utility functions.

This module contains unit tests for the utility functions in doc_ai_helper_backend.services.llm.utils.
"""

import pytest
from datetime import datetime
from typing import List

from doc_ai_helper_backend.models.llm import MessageItem, MessageRole
from doc_ai_helper_backend.services.llm.utils import (
    estimate_message_tokens,
    estimate_conversation_tokens,
    optimize_conversation_history,
    format_conversation_for_provider,
)


def test_estimate_message_tokens():
    """トークン推定機能のテスト"""
    # 基本的なメッセージのトークン数推定
    message = MessageItem(role=MessageRole.USER, content="これはテストメッセージです。")
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
    system_message = MessageItem(role=MessageRole.SYSTEM, content="システム指示です。")
    system_tokens = estimate_message_tokens(system_message)
    assert system_tokens > 0


def test_estimate_conversation_tokens():
    """会話全体のトークン推定機能のテスト"""
    # 空の会話履歴
    assert estimate_conversation_tokens([]) == 0

    # 単一メッセージの会話
    history = [MessageItem(role=MessageRole.USER, content="こんにちは")]
    assert estimate_conversation_tokens(history) > 0

    # 複数メッセージの会話
    history.append(MessageItem(role=MessageRole.ASSISTANT, content="どうぞ"))
    history.append(MessageItem(role=MessageRole.USER, content="質問があります"))
    multi_tokens = estimate_conversation_tokens(history)

    # 個別のトークン合計と比較
    individual_sum = (
        sum(estimate_message_tokens(msg) for msg in history) + 3
    )  # オーバーヘッド
    assert multi_tokens == individual_sum


def test_optimize_conversation_history():
    """会話履歴の最適化機能のテスト"""
    # 短い履歴（最適化不要）
    short_history = [
        MessageItem(role=MessageRole.USER, content="こんにちは"),
        MessageItem(role=MessageRole.ASSISTANT, content="どうぞ"),
    ]
    optimized = optimize_conversation_history(short_history, max_tokens=1000)
    assert len(optimized) == len(short_history)

    # リストのコピーが返されていることを確認
    assert optimized is not short_history
    assert [msg.content for msg in optimized] == [msg.content for msg in short_history]

    # 長い履歴（最適化が必要）- 多数の短いメッセージ
    long_history = [
        MessageItem(
            role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
            content=f"これはメッセージ {i} です。",
        )
        for i in range(20)
    ]

    # 最大トークンを厳しく制限して最適化
    optimized = optimize_conversation_history(
        long_history, max_tokens=100, preserve_recent=2
    )
    assert len(optimized) < len(long_history)

    # 最新のメッセージは保持されている
    assert optimized[-1].content == long_history[-1].content
    assert optimized[-2].content == long_history[-2].content

    # トークン数が制限以下であること（概算）
    assert estimate_conversation_tokens(optimized) <= 100

    # 非常に長いコンテンツを持つ会話の最適化
    verbose_history = [
        MessageItem(
            role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
            content=f"これは長いメッセージ {i} です。" * 50,
        )
        for i in range(5)
    ]

    optimized_verbose = optimize_conversation_history(
        verbose_history, max_tokens=500, preserve_recent=2
    )
    assert len(optimized_verbose) <= 3  # 長いメッセージなので削減される
    assert optimized_verbose[-2:] == verbose_history[-2:]  # 最新の2つは保持


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
