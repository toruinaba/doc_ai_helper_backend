"""
Test for MockLLMService with conversation history and repository context support.

This module contains unit tests for the MockLLMService implementation
with a focus on conversation history processing and repository context capabilities.
"""

import pytest
import asyncio
from typing import List

from doc_ai_helper_backend.models.llm import MessageItem, MessageRole, LLMResponse
from doc_ai_helper_backend.models.repository_context import (
    RepositoryContext,
    DocumentMetadata,
    GitService,
    DocumentType,
)
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


@pytest.mark.asyncio
async def test_mock_service_with_repository_context():
    """リポジトリコンテキストを使ったクエリのテスト"""
    service = MockLLMService(response_delay=0.01)

    # リポジトリコンテキストを作成
    repo_context = RepositoryContext(
        service=GitService.GITHUB,
        owner="microsoft",
        repo="vscode",
        ref="main",
        current_path="README.md",
    )

    # ドキュメントメタデータを作成
    doc_metadata = DocumentMetadata(
        title="Visual Studio Code",
        type=DocumentType.MARKDOWN,
        filename="README.md",
        file_size=2048,
    )

    # ドキュメントコンテンツ
    doc_content = """# Visual Studio Code
A powerful code editor for developers.
"""

    # コンテキスト付きクエリ
    response = await service.query(
        prompt="このファイルについて教えてください",
        repository_context=repo_context,
        document_metadata=doc_metadata,
        document_content=doc_content,
        system_prompt_template="contextual_document_assistant_ja",
        include_document_in_system_prompt=True,
    )

    assert isinstance(response, LLMResponse)
    assert response.content
    assert response.provider == "mock"

    # MockLLMServiceでは新しいパラメータは無視されるが、
    # エラーなく動作することを確認
    assert response.usage.prompt_tokens > 0


@pytest.mark.asyncio
async def test_mock_service_with_context_and_history():
    """コンテキストと会話履歴の組み合わせテスト"""
    service = MockLLMService(response_delay=0.01)

    # 会話履歴
    history = [
        MessageItem(role=MessageRole.USER, content="Hello"),
        MessageItem(role=MessageRole.ASSISTANT, content="Hi there!"),
    ]

    # リポジトリコンテキスト
    repo_context = RepositoryContext(
        service=GitService.GITLAB, owner="group", repo="project", ref="develop"
    )

    # ドキュメントメタデータ
    doc_metadata = DocumentMetadata(
        title="API Documentation", type=DocumentType.MARKDOWN, filename="api.md"
    )

    # 全てのパラメータを指定してクエリ
    response = await service.query(
        prompt="APIの使い方を教えてください",
        conversation_history=history,
        repository_context=repo_context,
        document_metadata=doc_metadata,
        document_content="# API Documentation\nThis is the API guide.",
        system_prompt_template="contextual_document_assistant_ja",
        include_document_in_system_prompt=True,
        options={"model": "custom-model"},
    )

    assert isinstance(response, LLMResponse)
    assert response.content
    assert response.model == "custom-model"  # オプションが反映される
    assert response.provider == "mock"


@pytest.mark.asyncio
async def test_mock_service_stream_query_with_context():
    """ストリーミングクエリでのコンテキストテスト"""
    service = MockLLMService(response_delay=0.01)

    # コンテキスト準備
    repo_context = RepositoryContext(
        service=GitService.GITHUB, owner="test", repo="example", ref="main"
    )

    doc_metadata = DocumentMetadata(
        title="Example Document", type=DocumentType.PYTHON, filename="main.py"
    )

    # ストリーミングクエリ
    chunks = []
    async for chunk in service.stream_query(
        prompt="コードの説明をお願いします",
        repository_context=repo_context,
        document_metadata=doc_metadata,
        document_content="print('Hello, World!')",
        system_prompt_template="contextual_document_assistant_ja",
    ):
        chunks.append(chunk)

    # ストリーミング結果の確認
    assert len(chunks) > 0
    full_content = "".join(chunks)
    assert len(full_content) > 0


@pytest.mark.asyncio
async def test_mock_service_context_parameter_combinations():
    """コンテキストパラメータの様々な組み合わせテスト"""
    service = MockLLMService(response_delay=0.01)

    # 1. repository_context のみ
    repo_context = RepositoryContext(
        service=GitService.BITBUCKET, owner="team", repo="project", ref="main"
    )

    response = await service.query(
        prompt="リポジトリについて教えて", repository_context=repo_context
    )
    assert isinstance(response, LLMResponse)

    # 2. document_metadata のみ
    doc_metadata = DocumentMetadata(
        title="Test Doc", type=DocumentType.HTML, filename="index.html"
    )

    response = await service.query(
        prompt="ドキュメントについて教えて", document_metadata=doc_metadata
    )
    assert isinstance(response, LLMResponse)

    # 3. document_content のみ
    response = await service.query(
        prompt="内容について教えて", document_content="This is a test document."
    )
    assert isinstance(response, LLMResponse)

    # 4. include_document_in_system_prompt = False
    response = await service.query(
        prompt="システムプロンプトなし",
        repository_context=repo_context,
        document_metadata=doc_metadata,
        document_content="Content",
        include_document_in_system_prompt=False,
    )
    assert isinstance(response, LLMResponse)

    # 5. カスタムテンプレート
    response = await service.query(
        prompt="カスタムテンプレート",
        repository_context=repo_context,
        system_prompt_template="custom_template",
    )
    assert isinstance(response, LLMResponse)


@pytest.mark.asyncio
async def test_mock_service_context_edge_cases():
    """コンテキスト機能のエッジケーステスト"""
    service = MockLLMService(response_delay=0.01)

    # 空の値でのテスト
    response = await service.query(
        prompt="空のコンテキスト",
        repository_context=None,
        document_metadata=None,
        document_content="",
        system_prompt_template="",
        include_document_in_system_prompt=True,
    )
    assert isinstance(response, LLMResponse)

    # 非常に長いコンテンツ
    long_content = "A" * 10000
    response = await service.query(
        prompt="長いコンテンツ", document_content=long_content
    )
    assert isinstance(response, LLMResponse)

    # 特殊文字を含むコンテキスト
    repo_context = RepositoryContext(
        service=GitService.GITHUB,
        owner="test-user",
        repo="special.repo-name_123",
        ref="feature/new-api",
        current_path="docs/API Reference.md",
    )

    response = await service.query(
        prompt="特殊文字テスト", repository_context=repo_context
    )
    assert isinstance(response, LLMResponse)
