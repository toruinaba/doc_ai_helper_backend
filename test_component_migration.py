"""
新しいコンポーネント構造の基本テスト

移行したコンポーネントが正常に動作することを確認するテストです。
"""

import pytest
from doc_ai_helper_backend.services.llm.components import (
    LLMCacheService,
    PromptTemplateManager,
    MessageBuilder,
    FunctionService,
    ResponseBuilder,
    TokenCounter,
    StreamingUtils,
    QueryManager,
)
from doc_ai_helper_backend.models.llm import LLMResponse, LLMUsage, MessageRole


class TestComponentStructure:
    """コンポーネント構造の基本テスト"""

    def test_cache_service_basic_functionality(self):
        """キャッシュサービスの基本機能テスト"""
        cache = LLMCacheService(ttl_seconds=60)

        # キーの生成テスト
        key = cache.generate_key("test prompt", {"temperature": 0.7})
        assert isinstance(key, str)
        assert len(key) == 32  # MD5ハッシュの長さ

        # 統計情報のテスト
        stats = cache.stats()
        assert "total_items" in stats
        assert "ttl_seconds" in stats
        assert stats["ttl_seconds"] == 60

    def test_template_manager_basic_functionality(self):
        """テンプレートマネージャーの基本機能テスト"""
        manager = PromptTemplateManager()

        # テンプレートリストの取得
        templates = manager.list_templates()
        assert isinstance(templates, list)

        # テンプレートの検証
        template_data = {
            "id": "test_template",
            "template": "Hello {{name}}!",
            "variables": [{"name": "name", "required": True}],
        }

        errors = manager.validate_template(template_data)
        assert len(errors) == 0

    def test_message_builder_basic_functionality(self):
        """メッセージビルダーの基本機能テスト"""
        builder = MessageBuilder()

        # システムメッセージの作成
        system_msg = builder.create_system_message("You are a helpful assistant")
        assert system_msg.role == MessageRole.SYSTEM
        assert "helpful assistant" in system_msg.content

        # ユーザーメッセージの作成
        user_msg = builder.create_user_message("Hello, world!")
        assert user_msg.role == MessageRole.USER
        assert user_msg.content == "Hello, world!"

        # API形式への変換
        messages = [system_msg, user_msg]
        api_messages = builder.format_messages_for_api(messages)
        assert len(api_messages) == 2
        assert api_messages[0]["role"] == "system"
        assert api_messages[1]["role"] == "user"

    def test_function_service_basic_functionality(self):
        """関数サービスの基本機能テスト"""
        service = FunctionService()

        # テスト関数の定義
        def test_function(x: int, y: int) -> int:
            return x + y

        # 関数の登録
        service.register_function(
            "add",
            test_function,
            "Add two numbers",
            {
                "type": "object",
                "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}},
                "required": ["x", "y"],
            },
        )

        # 利用可能な関数の確認
        functions = service.get_available_functions()
        assert len(functions) == 1
        assert functions[0].name == "add"

        # API用準備
        api_functions = service.prepare_functions_for_api()
        assert len(api_functions) == 1
        assert api_functions[0]["type"] == "function"

    def test_response_builder_basic_functionality(self):
        """レスポンスビルダーの基本機能テスト"""
        builder = ResponseBuilder()

        # モックレスポンスの作成
        response = builder.build_mock_response(
            content="Hello, world!", model="test-model"
        )

        assert isinstance(response, LLMResponse)
        assert response.content == "Hello, world!"
        assert response.model == "test-model"
        assert response.provider == "mock"
        assert isinstance(response.usage, LLMUsage)

    def test_token_counter_basic_functionality(self):
        """トークンカウンターの基本機能テスト"""
        counter = TokenCounter()

        # テキストのトークン数推定
        tokens = counter.estimate_text_tokens("Hello, world!")
        assert isinstance(tokens, int)
        assert tokens > 0

        # メッセージのトークン数推定
        from doc_ai_helper_backend.models.llm import MessageItem
        from datetime import datetime

        message = MessageItem(
            role=MessageRole.USER, content="Hello, world!", timestamp=datetime.now()
        )

        message_tokens = counter.estimate_message_tokens(message)
        assert isinstance(message_tokens, int)
        assert message_tokens > tokens  # ロールオーバーヘッドが含まれる

    @pytest.mark.asyncio
    async def test_streaming_utils_basic_functionality(self):
        """ストリーミングユーティリティの基本機能テスト"""
        utils = StreamingUtils()

        # コンテンツのチャンク化
        content = "Hello, world! This is a test."
        chunks = []

        async for chunk in utils.chunk_content(
            content, chunk_size=5, delay_per_chunk=0
        ):
            chunks.append(chunk)

        assert len(chunks) > 1
        assert "".join(chunks) == content

        # モックストリームの作成
        mock_chunks = []
        async for chunk in utils.create_mock_stream(
            "Test content", chunk_size=4, delay=0
        ):
            mock_chunks.append(chunk)

        assert "".join(mock_chunks) == "Test content"

    def test_query_manager_basic_functionality(self):
        """クエリマネージャーの基本機能テスト"""
        manager = QueryManager()

        # コンテキスト準備
        context = manager.prepare_context(custom_instructions="Be helpful")
        assert "custom_instructions" in context
        assert context["custom_instructions"] == "Be helpful"

        # クエリオプションの検証
        valid_options = {"messages": [{"role": "user", "content": "Hello"}]}

        errors = manager.validate_query_options(valid_options)
        assert len(errors) == 0

        # 無効なオプションの検証
        invalid_options = {"messages": "invalid"}  # リストではない

        errors = manager.validate_query_options(invalid_options)
        assert len(errors) > 0

    def test_component_integration(self):
        """コンポーネント間の統合テスト"""
        # 複数のコンポーネントを組み合わせて使用
        cache = LLMCacheService()
        template_manager = PromptTemplateManager()
        message_builder = MessageBuilder()

        query_manager = QueryManager(
            cache_service=cache,
            template_manager=template_manager,
            message_builder=message_builder,
        )

        # 統合されたマネージャーが正常に動作することを確認
        assert query_manager.cache_service is cache
        assert query_manager.template_manager is template_manager
        assert query_manager.message_builder is message_builder


class TestBackwardCompatibility:
    """後方互換性のテスト"""

    def test_response_builder_alias(self):
        """LLMResponseBuilderエイリアスのテスト"""
        from doc_ai_helper_backend.services.llm.components import LLMResponseBuilder

        # エイリアスが正常に動作することを確認
        builder = LLMResponseBuilder()
        response = builder.build_mock_response("Test")
        assert isinstance(response, LLMResponse)

    def test_module_level_functions(self):
        """モジュールレベル関数の後方互換性テスト"""
        from doc_ai_helper_backend.services.llm.components.tokens import (
            estimate_message_tokens,
            estimate_conversation_tokens,
        )
        from doc_ai_helper_backend.models.llm import MessageItem, MessageRole
        from datetime import datetime

        # メッセージトークン推定
        tokens = estimate_message_tokens("Hello, world!")
        assert isinstance(tokens, int)
        assert tokens > 0

        # 会話トークン推定
        messages = [
            MessageItem(
                role=MessageRole.USER, content="Hello", timestamp=datetime.now()
            )
        ]

        conv_tokens = estimate_conversation_tokens(messages)
        assert isinstance(conv_tokens, int)
        assert conv_tokens > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
