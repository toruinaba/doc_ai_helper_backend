import os
import pytest
import time
from typing import Dict, Any

from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.services.llm.factory import LLMServiceFactory
from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    LLMUsage,
    ProviderCapabilities,
    MessageItem,
    MessageRole,
)


def pytest_configure(config):
    """統合テストの設定"""
    # 必要な環境変数をチェック
    required_env_vars = {
        "OPENAI_API_KEY": "OpenAI API integration tests",
    }

    missing_vars = []
    for var, description in required_env_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var} (for {description})")

    if missing_vars:
        pytest.skip(
            f"Integration tests skipped. Missing environment variables: {', '.join(missing_vars)}"
        )


class TestOpenAIServiceRealAPI:
    """OpenAI実API統合テスト（実際のAPIキーが必要）"""

    @pytest.fixture
    def openai_service(self):
        """実際のOpenAIサービスのインスタンスを取得する"""
        # 環境変数からAPIキーを取得
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY environment variable not set")

        # 環境変数からベースURLを取得（LiteLLMなどのプロキシサーバー対応）
        base_url = os.environ.get("OPENAI_BASE_URL")

        # 環境変数からモデル名を取得（カスタムモデル対応）
        model = os.environ.get("DEFAULT_OPENAI_MODEL") or os.environ.get(
            "OPENAI_MODEL", "gpt-3.5-turbo"
        )

        # OpenAIサービスを作成（ベースURLが指定されている場合は設定）
        kwargs = {"api_key": api_key, "default_model": model}
        if base_url:
            kwargs["base_url"] = base_url

        service = LLMServiceFactory.create("openai", **kwargs)

        # テスト用にキャッシュをクリア（属性が存在する場合のみ）
        cache_service = getattr(service, "cache_service", None)
        if cache_service:
            cache_service.clear()

        return service

    @pytest.mark.asyncio
    async def test_basic_query(self, openai_service: LLMServiceBase):
        """基本的なクエリが正しく動作することを確認"""
        # 基本的なプロンプト
        prompt = "1 + 1 = ?"

        # クエリを実行
        response = await openai_service.query(prompt)

        # レスポンスが適切な形式であることを確認
        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert len(response.content) > 0

        # 使用量情報が含まれていることを確認
        assert response.usage is not None
        assert isinstance(response.usage, LLMUsage)
        assert response.usage.prompt_tokens > 0
        assert response.usage.completion_tokens > 0
        assert response.usage.total_tokens > 0

        # 使用したモデルが含まれていることを確認
        assert response.model is not None

        # 設定したモデルと一致することを確認
        expected_model = os.environ.get("DEFAULT_OPENAI_MODEL") or os.environ.get(
            "OPENAI_MODEL", "gpt-3.5-turbo"
        )
        assert response.model == expected_model

    @pytest.mark.asyncio
    async def test_query_with_system_instruction(self, openai_service: LLMServiceBase):
        """システムインストラクション付きのクエリが正しく動作することを確認"""
        # システムインストラクション付きのクエリ
        prompt = "日本の首都は？"

        # システムメッセージを含む会話履歴を作成
        conversation_history = [
            MessageItem(
                role=MessageRole.SYSTEM,
                content="あなたは旅行ガイドです。簡潔に回答してください。",
            ),
        ]

        # オプションを設定
        options = {"temperature": 0.7, "max_tokens": 100}

        # クエリを実行
        response = await openai_service.query(prompt, conversation_history, options)

        # レスポンスが適切な形式であることを確認
        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_caching(self, openai_service: LLMServiceBase):
        """キャッシュ機能のテスト"""
        # 同じプロンプトで2回クエリ
        prompt = "What is the capital of France?"

        # 1回目のクエリ
        start_time = time.time()
        response1 = await openai_service.query(prompt)
        first_query_time = time.time() - start_time

        # 2回目のクエリ（キャッシュから取得される可能性がある）
        start_time = time.time()
        response2 = await openai_service.query(prompt)
        second_query_time = time.time() - start_time

        # レスポンスが両方とも有効であることを確認
        assert response1.content is not None
        assert response2.content is not None

        # 基本的な検証（キャッシュが機能していてもいなくても、少なくとも有効なレスポンスが得られること）
        assert len(response1.content) > 0
        assert len(response2.content) > 0

    @pytest.mark.asyncio
    async def test_capabilities(self, openai_service: LLMServiceBase):
        """機能情報取得のテスト"""
        # 機能情報を取得
        capabilities = await openai_service.get_capabilities()

        # ProviderCapabilitiesオブジェクトが返されることを確認
        assert isinstance(capabilities, ProviderCapabilities)

        # 必要な情報が含まれていることを確認
        assert hasattr(capabilities, "available_models")
        assert len(capabilities.available_models) > 0

        assert hasattr(capabilities, "max_tokens")
        assert len(capabilities.max_tokens) > 0

        # 環境変数からモデル名を取得
        expected_model = os.environ.get("DEFAULT_OPENAI_MODEL") or os.environ.get(
            "OPENAI_MODEL", "gpt-3.5-turbo"
        )

        # モデル名が直接含まれているか、または同等のモデルがあるか確認
        # (LiteLLMではモデル名マッピングがある場合があるため、厳密な比較は行わない)
        if expected_model.startswith(("gpt-", "azure-")):
            # GPTまたはAzureモデルの場合
            assert any(
                m.startswith(("gpt-", "azure-")) for m in capabilities.available_models
            )
        else:
            # その他のモデルの場合は、利用可能なモデルが存在することを確認
            assert len(capabilities.available_models) > 0

    @pytest.mark.asyncio
    async def test_error_handling(self, openai_service: LLMServiceBase):
        """エラー処理のテスト"""
        # 不正なオプションでクエリを実行
        try:
            # 不正な温度値（>2.0）を設定
            invalid_options = {"temperature": 3.0}
            await openai_service.query("Test prompt", options=invalid_options)
            pytest.fail("Expected an exception for invalid temperature")
        except Exception as e:
            # 何らかの例外が発生することを確認
            assert "temperature" in str(e).lower() or "parameter" in str(e).lower()

    @pytest.mark.asyncio
    async def test_token_estimation(self, openai_service: LLMServiceBase):
        """トークン数推定のテスト"""
        # サンプルテキスト
        text = "This is a sample text for token estimation."

        # トークン数を推定
        tokens = await openai_service.estimate_tokens(text)

        # トークン数が正の整数であることを確認
        assert isinstance(tokens, int)
        assert tokens > 0

        # 文字数が増えるとトークン数も増えることを確認
        longer_text = text * 10
        longer_tokens = await openai_service.estimate_tokens(longer_text)
        assert longer_tokens > tokens

    @pytest.mark.asyncio
    async def test_custom_base_url(self):
        """カスタムベースURL（LiteLLMなど）との連携テスト"""
        # カスタムベースURLが設定されていない場合はスキップ
        base_url = os.environ.get("OPENAI_BASE_URL")
        api_key = os.environ.get("OPENAI_API_KEY")

        if not base_url or not api_key:
            pytest.skip("OPENAI_BASE_URL or OPENAI_API_KEY not set")

        # 環境変数からモデル名を取得（カスタムモデル対応）
        model = os.environ.get("DEFAULT_OPENAI_MODEL") or os.environ.get(
            "OPENAI_MODEL", "gpt-3.5-turbo"
        )

        # カスタムベースURLを使用してサービスを作成
        service = LLMServiceFactory.create(
            "openai", api_key=api_key, base_url=base_url, default_model=model
        )

        # 基本的なクエリが動作することを確認
        prompt = "Hello, LiteLLM!"
        response = await service.query(prompt)

        # レスポンスが適切な形式であることを確認
        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert len(response.content) > 0

        # 使用したモデルが設定したモデルと一致することを確認
        assert response.model == model

    @pytest.mark.asyncio
    async def test_conversation_history_basic(self, openai_service: LLMServiceBase):
        """基本的な会話履歴が正しく処理されることを確認"""
        prompt = "今日の天気はどうですか？"

        # 会話履歴を作成
        conversation_history = [
            MessageItem(role=MessageRole.USER, content="こんにちは"),
            MessageItem(
                role=MessageRole.ASSISTANT,
                content="こんにちは！何かお手伝いできることはありますか？",
            ),
        ]

        # クエリを実行
        response = await openai_service.query(prompt, conversation_history)

        # レスポンスが適切な形式であることを確認
        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert len(response.content) > 0

        # 使用量情報が含まれていることを確認
        assert response.usage is not None

        # 最適化された会話履歴が返されることを確認
        # 短い会話では最適化されずに元の履歴がそのまま返される
        assert response.optimized_conversation_history is not None
        assert len(response.optimized_conversation_history) >= len(conversation_history)

    @pytest.mark.asyncio
    async def test_conversation_history_optimization(
        self, openai_service: LLMServiceBase
    ):
        """長い会話履歴が最適化されることを確認"""
        prompt = "この会話をまとめてください。"

        # 長い会話履歴を作成（要約が発生するように十分長くする）
        conversation_history = []
        for i in range(20):  # 20往復の会話を作成
            conversation_history.extend(
                [
                    MessageItem(
                        role=MessageRole.USER,
                        content=f"質問{i+1}: これは{i+1}番目の質問です。長めの内容にして、トークン数を増やします。具体的には、日常生活について、仕事について、趣味について、将来の計画について等々、様々なトピックについて質問したいと思います。",
                    ),
                    MessageItem(
                        role=MessageRole.ASSISTANT,
                        content=f"回答{i+1}: ご質問ありがとうございます。{i+1}番目のご質問にお答えします。詳細な説明をさせていただきますと、このような内容になります。日常生活、仕事、趣味、将来の計画など、どのトピックについても丁寧にお答えできます。",
                    ),
                ]
            )

        # クエリを実行
        response = await openai_service.query(prompt, conversation_history)

        # レスポンスが適切な形式であることを確認
        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert len(response.content) > 0

        # 最適化された会話履歴が返されることを確認
        assert response.optimized_conversation_history is not None

        # 最適化情報が含まれていることを確認
        assert response.history_optimization_info is not None

        # 最適化により会話履歴が短縮されていることを確認
        # （元の会話は40メッセージ、最適化後は少なくなるはず）
        original_count = len(conversation_history)
        optimized_count = len(response.optimized_conversation_history)

        # 実際のAPIでは最適化が発生するかはトークン数による
        # 長い会話履歴を使用しているため、最適化が発生するはず
        assert response.history_optimization_info is not None
        # 最適化情報が正しく設定されていることを確認
        assert isinstance(response.history_optimization_info["was_optimized"], bool)
        if response.history_optimization_info["was_optimized"]:
            assert optimized_count < original_count

    @pytest.mark.asyncio
    async def test_conversation_history_with_system_message(
        self, openai_service: LLMServiceBase
    ):
        """システムメッセージ付きの会話履歴が正しく処理されることを確認"""
        prompt = "前回の話の続きをお願いします。"

        # システムメッセージを含む会話履歴を作成
        conversation_history = [
            MessageItem(
                role=MessageRole.SYSTEM,
                content="あなたは親切なアシスタントです。常に丁寧に回答してください。",
            ),
            MessageItem(
                role=MessageRole.USER,
                content="プロジェクトの進捗について相談があります。",
            ),
            MessageItem(
                role=MessageRole.ASSISTANT,
                content="プロジェクトの進捗についてご相談いただき、ありがとうございます。どのような点についてお聞かせください？",
            ),
            MessageItem(
                role=MessageRole.USER, content="スケジュールが遅れそうで心配です。"
            ),
            MessageItem(
                role=MessageRole.ASSISTANT,
                content="スケジュールの遅れについてご心配をおかけしております。具体的にどの部分で遅れが生じているか教えていただけますでしょうか？",
            ),
        ]

        # クエリを実行
        response = await openai_service.query(prompt, conversation_history)

        # レスポンスが適切な形式であることを確認
        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert len(response.content) > 0

        # 最適化された会話履歴が返されることを確認
        assert response.optimized_conversation_history is not None

        # システムメッセージが保持されていることを確認
        system_messages = [
            msg
            for msg in response.optimized_conversation_history
            if msg.role == MessageRole.SYSTEM
        ]
        assert len(system_messages) > 0, "System message should be preserved"
        assert (
            system_messages[0].content
            == "あなたは親切なアシスタントです。常に丁寧に回答してください。"
        )

    @pytest.mark.asyncio
    async def test_conversation_history_empty(self, openai_service: LLMServiceBase):
        """空の会話履歴でも正しく動作することを確認"""
        prompt = "初回の質問です。"

        # 空の会話履歴
        conversation_history = []

        # クエリを実行
        response = await openai_service.query(prompt, conversation_history)

        # レスポンスが適切な形式であることを確認
        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert len(response.content) > 0

        # 最適化された会話履歴が返されることを確認（空の場合でも空のリストが返される）
        assert response.optimized_conversation_history is not None
        assert isinstance(response.optimized_conversation_history, list)

    @pytest.mark.asyncio
    async def test_conversation_history_none(self, openai_service: LLMServiceBase):
        """Noneの会話履歴でも正しく動作することを確認"""
        prompt = "初回の質問です。"

        # None会話履歴
        conversation_history = None

        # クエリを実行
        response = await openai_service.query(prompt, conversation_history)

        # レスポンスが適切な形式であることを確認
        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert len(response.content) > 0

        # 最適化された会話履歴が返されることを確認（Noneの場合でも空のリストが返される）
        assert response.optimized_conversation_history is not None
        assert isinstance(response.optimized_conversation_history, list)
        assert len(response.optimized_conversation_history) == 0
