"""
Test for MockLLMService with conversation history support.

This module contains unit tests for the MockLLMService implementation
with a focus on conversation history processing capabilities.
"""

import pytest
import asyncio
from typing import List

from doc_ai_helper_backend.models.llm import MessageItem, MessageRole, LLMResponse
from doc_ai_helper_backend.services.llm.mock_service import MockLLMService


@pytest.mark.asyncio
async def test_mock_service_basic():
    """基本的なMockLLMServiceのテスト"""
    # サービスインスタンスの作成（遅延を短く）
    service = MockLLMService(response_delay=0.01)

    # 会話履歴なしの基本クエリ
    response = await service.query("こんにちは")
    assert isinstance(response, LLMResponse)
    assert response.content  # 空でないことを確認
    assert response.model  # モデル名が設定されている
    assert response.provider == "mock"

    # 組み込みパターンのテスト
    response = await service.query("help")
    assert "mock" in response.content.lower()

    # トークン使用量の確認
    assert response.usage.prompt_tokens > 0
    assert response.usage.completion_tokens > 0
    assert (
        response.usage.total_tokens
        == response.usage.prompt_tokens + response.usage.completion_tokens
    )


@pytest.mark.asyncio
async def test_mock_service_with_conversation_history():
    """会話履歴を使ったクエリのテスト"""
    # サービスインスタンスの作成
    service = MockLLMService(response_delay=0.01)

    # 会話履歴を作成
    history = [
        MessageItem(role=MessageRole.USER, content="こんにちは"),
        MessageItem(role=MessageRole.ASSISTANT, content="こんにちは、どうぞ"),
        MessageItem(
            role=MessageRole.USER, content="ドキュメントについて質問があります"
        ),
        MessageItem(role=MessageRole.ASSISTANT, content="はい、どうぞ"),
    ]

    # 会話履歴を使ったクエリ
    response = await service.query(
        "前の質問は何でしたか？", conversation_history=history
    )
    assert isinstance(response, LLMResponse)
    assert "ドキュメントについて質問があります" in response.content

    # 前回の回答を尋ねる
    response = await service.query("前の回答は？", conversation_history=history)
    assert "はい、どうぞ" in response.content

    # 会話履歴の長さに言及する
    response = await service.query(
        "この会話は何回目ですか？", conversation_history=history
    )
    assert (
        "4" in response.content or "４" in response.content or "四" in response.content
    )


@pytest.mark.asyncio
async def test_mock_service_system_instructions():
    """システム指示を含む会話履歴のテスト"""
    service = MockLLMService(response_delay=0.01)

    # システム指示を含む会話履歴
    history = [
        MessageItem(
            role=MessageRole.SYSTEM, content="あなたは親切なアシスタントです。"
        ),
        MessageItem(role=MessageRole.USER, content="こんにちは"),
        MessageItem(
            role=MessageRole.ASSISTANT, content="こんにちは！どうぞお手伝いします。"
        ),
    ]

    # 通常のクエリ
    response = await service.query("ヘルプ", conversation_history=history)
    assert isinstance(response, LLMResponse)

    # 会話履歴の要約が含まれていることを確認
    assert "[system]" in response.content or "system" in response.content.lower()


@pytest.mark.asyncio
async def test_stream_query_with_conversation_history():
    """会話履歴を使ったストリーミングクエリのテスト"""
    service = MockLLMService(response_delay=0.01)

    # 会話履歴
    history = [
        MessageItem(role=MessageRole.USER, content="こんにちは"),
        MessageItem(role=MessageRole.ASSISTANT, content="こんにちは、どうぞ"),
    ]

    # ストリーミングレスポンスの収集
    chunks = []
    async for chunk in service.stream_query("help", conversation_history=history):
        chunks.append(chunk)

    # 少なくとも数チャンクが返されることを確認
    assert len(chunks) > 1

    # 全チャンクを結合して完全な応答を取得
    full_response = "".join(chunks)
    assert "mock" in full_response.lower()

    # 会話履歴の考慮が反映されている
    assert "会話履歴" in full_response or "context" in full_response.lower()


@pytest.mark.asyncio
async def test_mock_service_edge_cases():
    """エッジケースのテスト"""
    service = MockLLMService()

    # 空の会話履歴
    empty_history = []
    response = await service.query("こんにちは", conversation_history=empty_history)
    assert isinstance(response, LLMResponse)

    # 非常に長い会話履歴
    long_history = [
        MessageItem(
            role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
            content=f"メッセージ {i}",
        )
        for i in range(30)
    ]

    response = await service.query("こんにちは", conversation_history=long_history)
    assert isinstance(response, LLMResponse)

    # オプションと会話履歴の両方を指定
    response = await service.query(
        "hello", conversation_history=long_history, options={"model": "custom-model"}
    )
    assert response.model == "custom-model"

    # エラーパターン
    response = await service.query("error", conversation_history=long_history)
    assert "error" in response.content.lower() or "エラー" in response.content
