import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import json
from typing import Dict, Any

from doc_ai_helper_backend.services.llm.openai_service import OpenAIService
from doc_ai_helper_backend.services.llm.cache_service import LLMCacheService
from doc_ai_helper_backend.models.llm import LLMResponse, LLMUsage, ProviderCapabilities


class TestOpenAIService:
    """OpenAIServiceの単体テスト"""

    @pytest.fixture
    def openai_service(self, monkeypatch):
        """テスト用OpenAIServiceインスタンス"""
        # モックレスポンスの設定
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Mock response"
        mock_completion.usage.prompt_tokens = 10
        mock_completion.usage.completion_tokens = 20
        mock_completion.usage.total_tokens = 30
        mock_completion.model_dump.return_value = {"mock": "response"}

        # AsyncOpenAIクライアントのモック
        mock_async_client = MagicMock()
        mock_async_client.chat.completions.create = AsyncMock(
            return_value=mock_completion
        )

        # OpenAIクライアントのモック
        mock_sync_client = MagicMock()

        # tiktokenのモック
        mock_encoder = MagicMock()
        mock_encoder.encode.return_value = [1, 2, 3]  # トークン数のダミーデータ

        # パッチ適用
        # 重要: クラス全体ではなく、コンストラクタをモックすることで、
        # OpenAIServiceのコンストラクタ内で新しいクライアントが生成されないようにする
        def mock_async_openai(**kwargs):
            return mock_async_client

        def mock_sync_openai(**kwargs):
            return mock_sync_client

        monkeypatch.setattr("openai.AsyncOpenAI", mock_async_openai)
        monkeypatch.setattr("openai.OpenAI", mock_sync_openai)
        monkeypatch.setattr("tiktoken.encoding_for_model", lambda model: mock_encoder)
        monkeypatch.setattr("tiktoken.get_encoding", lambda encoding: mock_encoder)

        # サービスインスタンス作成
        service = OpenAIService(api_key="test-api-key", default_model="gpt-3.5-turbo")

        # 既存のクライアントをモックで上書き（念のため）
        service.async_client = mock_async_client
        service.sync_client = mock_sync_client

        # テスト用にキャッシュをクリア
        service.cache_service.clear()

        return service

    @pytest.mark.asyncio
    async def test_initialization(self, openai_service):
        """サービスの初期化をテスト"""
        # 基本的なプロパティが正しく設定されていることを確認
        assert openai_service.api_key == "test-api-key"
        assert openai_service.default_model == "gpt-3.5-turbo"
        assert openai_service.base_url is None

        # クライアントオブジェクトが存在することを確認
        assert openai_service.async_client is not None
        assert openai_service.sync_client is not None

    @pytest.mark.asyncio
    async def test_query_basic(self, openai_service):
        """基本的なクエリをテスト"""
        # クエリを実行
        response = await openai_service.query("Test prompt")

        # レスポンスが適切な形式であることを確認
        assert isinstance(response, LLMResponse)
        assert response.content == "Mock response"
        assert response.model == "gpt-3.5-turbo"
        assert response.provider == "openai"

        # 使用量情報が正しいことを確認
        assert response.usage.prompt_tokens == 10
        assert response.usage.completion_tokens == 20
        assert response.usage.total_tokens == 30

        # APIが正しいパラメータで呼び出されたことを確認
        assert openai_service.async_client.chat.completions.create.called
        call_args = openai_service.async_client.chat.completions.create.call_args[1]
        assert call_args["model"] == "gpt-3.5-turbo"
        assert call_args["messages"] == [{"role": "user", "content": "Test prompt"}]

    @pytest.mark.asyncio
    async def test_query_with_custom_options(self, openai_service):
        """カスタムオプション付きのクエリをテスト"""
        # カスタムオプションを設定
        options = {"temperature": 0.5, "max_tokens": 500, "model": "gpt-4"}

        # クエリを実行
        response = await openai_service.query("Test prompt", options)

        # レスポンスが適切な形式であることを確認
        assert response.model == "gpt-4"  # カスタムモデルが使用されていることを確認

        # APIが正しいパラメータで呼び出されたことを確認
        call_args = openai_service.async_client.chat.completions.create.call_args[1]
        assert call_args["temperature"] == 0.5
        assert call_args["max_tokens"] == 500
        assert call_args["model"] == "gpt-4"

    @pytest.mark.asyncio
    async def test_query_with_messages(self, openai_service):
        """messagesオプション付きのクエリをテスト"""
        # messagesを含むオプションを設定
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Tell me a joke"},
        ]
        options = {"messages": messages}

        # クエリを実行
        response = await openai_service.query("Ignored prompt", options)

        # APIが正しいパラメータで呼び出されたことを確認
        call_args = openai_service.async_client.chat.completions.create.call_args[1]
        assert call_args["messages"] == messages

    @pytest.mark.asyncio
    async def test_caching(self, openai_service):
        """キャッシュ機能をテスト"""
        # 同じプロンプトで2回クエリ
        prompt = "Cache test prompt"

        # 1回目のクエリ
        response1 = await openai_service.query(prompt)

        # APIが呼び出されたことを確認
        assert openai_service.async_client.chat.completions.create.call_count == 1

        # 2回目のクエリ（キャッシュから取得されるはず）
        response2 = await openai_service.query(prompt)

        # APIが再度呼び出されていないことを確認（キャッシュヒット）
        assert openai_service.async_client.chat.completions.create.call_count == 1

        # レスポンスが同じであることを確認
        assert response1.content == response2.content

    @pytest.mark.asyncio
    async def test_cache_different_options(self, openai_service):
        """異なるオプションでのキャッシュ動作をテスト"""
        # 同じプロンプトで異なるオプションを使用
        prompt = "Cache test prompt"

        # テスト前にカウントをリセット
        openai_service.async_client.chat.completions.create.reset_mock()

        # 1回目のクエリ
        await openai_service.query(prompt, {"temperature": 0.7})

        # 2回目のクエリ（異なるオプション）
        await openai_service.query(prompt, {"temperature": 0.8})

        # オプションが異なるため、APIが2回呼び出されていることを確認
        assert openai_service.async_client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_base_url_custom(self, monkeypatch):
        """カスタムベースURLでのサービス初期化をテスト"""
        # AsyncOpenAIとOpenAIのモック
        mock_async_client = MagicMock()
        mock_sync_client = MagicMock()

        # モックエンコーダ
        mock_encoder = MagicMock()
        mock_encoder.encode.return_value = [1, 2, 3]

        # モックを設定
        monkeypatch.setattr("openai.AsyncOpenAI", lambda **kwargs: mock_async_client)
        monkeypatch.setattr("openai.OpenAI", lambda **kwargs: mock_sync_client)
        monkeypatch.setattr("tiktoken.encoding_for_model", lambda model: mock_encoder)
        monkeypatch.setattr("tiktoken.get_encoding", lambda encoding: mock_encoder)

        # カスタムベースURLでサービスを初期化
        service = OpenAIService(
            api_key="test-api-key",
            default_model="gpt-3.5-turbo",
            base_url="https://litellm-proxy.example.com/v1",
        )

        # 正しいパラメータが渡されたことを確認
        # base_urlが正しく設定されていることを確認
        assert service.base_url == "https://litellm-proxy.example.com/v1"

    @pytest.mark.asyncio
    async def test_get_capabilities(self, openai_service):
        """機能情報取得をテスト"""
        # 機能情報を取得
        capabilities = await openai_service.get_capabilities()

        # 適切なオブジェクトが返されることを確認
        assert isinstance(capabilities, ProviderCapabilities)

        # 必要な情報が含まれていることを確認
        assert "gpt-3.5-turbo" in capabilities.available_models
        assert "gpt-4" in capabilities.available_models
        assert capabilities.max_tokens["gpt-3.5-turbo"] > 0
        assert capabilities.supports_streaming is True

    @pytest.mark.asyncio
    async def test_estimate_tokens(self, openai_service):
        """トークン数推定をテスト"""
        # サンプルテキスト
        text = "This is a sample text."

        # トークン数を推定
        tokens = await openai_service.estimate_tokens(text)

        # 結果が期待通りであることを確認
        assert tokens == 3  # モックエンコーダーの戻り値の長さ

    @pytest.mark.asyncio
    async def test_error_handling(self, openai_service):
        """エラーハンドリングをテスト"""
        # APIエラーをシミュレート
        openai_service.async_client.chat.completions.create.side_effect = Exception(
            "API error"
        )

        # エラーが適切に処理されることを確認
        with pytest.raises(Exception) as excinfo:
            await openai_service.query("Error test prompt")

        assert "API error" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_prepare_options(self, openai_service):
        """オプション準備ロジックをテスト"""
        # 基本的なプロンプトとオプション
        prompt = "Test prompt"
        options = {"temperature": 0.5, "max_tokens": 500, "model": "gpt-4"}

        # オプションを準備
        prepared_options = openai_service._prepare_options(prompt, options)

        # 期待通りのオプションが生成されることを確認
        assert prepared_options["temperature"] == 0.5
        assert prepared_options["max_tokens"] == 500
        assert prepared_options["model"] == "gpt-4"
        assert prepared_options["messages"] == [{"role": "user", "content": prompt}]

        # デフォルト値が上書きされていることを確認
        prepared_options_default = openai_service._prepare_options(prompt, {})
        assert prepared_options_default["temperature"] == 0.7  # デフォルト値
        assert prepared_options_default["model"] == "gpt-3.5-turbo"  # デフォルトモデル

    @pytest.mark.asyncio
    async def test_convert_to_llm_response(self, openai_service):
        """OpenAIレスポンスの変換をテスト"""
        # モックOpenAIレスポンス
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 15
        mock_response.model_dump.return_value = {"test": "data"}

        # レスポンスを変換
        llm_response = openai_service._convert_to_llm_response(mock_response, "gpt-4")

        # 変換結果が期待通りであることを確認
        assert isinstance(llm_response, LLMResponse)
        assert llm_response.content == "Test response"
        assert llm_response.model == "gpt-4"
        assert llm_response.provider == "openai"
        assert llm_response.usage.prompt_tokens == 5
        assert llm_response.usage.completion_tokens == 10
        assert llm_response.usage.total_tokens == 15
        assert llm_response.raw_response == {"test": "data"}

    @pytest.mark.asyncio
    async def test_stream_query(self, openai_service, monkeypatch):
        """ストリーミングクエリのテスト"""
        # ストリーミングレスポンスのモック
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock()]
        mock_chunk1.choices[0].delta.content = "Hello"

        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock()]
        mock_chunk2.choices[0].delta.content = " world"

        mock_chunk3 = MagicMock()
        mock_chunk3.choices = [MagicMock()]
        mock_chunk3.choices[0].delta.content = "!"

        # ストリーミングレスポンスを返すAsyncGeneratorのモック
        async def mock_stream():
            yield mock_chunk1
            yield mock_chunk2
            yield mock_chunk3

        # AsyncOpenAIクライアントのchat.completions.createメソッドをモック
        openai_service.async_client.chat.completions.create = AsyncMock(
            return_value=mock_stream()
        )

        # テスト実行
        chunks = []
        async for chunk in openai_service.stream_query("Test streaming"):
            chunks.append(chunk)

        # 検証
        assert chunks == ["Hello", " world", "!"]
        assert openai_service.async_client.chat.completions.create.call_count == 1
        # ストリーミングパラメータが設定されているか確認
        call_kwargs = openai_service.async_client.chat.completions.create.call_args[1]
        assert call_kwargs.get("stream") is True
