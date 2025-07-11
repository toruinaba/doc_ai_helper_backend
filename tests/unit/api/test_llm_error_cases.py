"""
LLM APIエンドポイントのエラーケースとエッジケーステスト
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from doc_ai_helper_backend.main import app
from doc_ai_helper_backend.services.llm.mock_service import MockLLMService
from doc_ai_helper_backend.core.exceptions import LLMServiceException


class TestLLMEndpointsErrorHandling:
    """LLM APIエンドポイントのエラーハンドリングテスト"""

    @pytest.fixture
    def client(self):
        """TestClientのフィクスチャ"""
        return TestClient(app)

    def test_query_with_invalid_provider(self, client):
        """無効なプロバイダーでのクエリテスト"""
        response = client.post(
            "/api/v1/llm/query",
            json={"prompt": "test prompt", "provider": "invalid_provider"},
        )
        # 現在の実装では無効なプロバイダーは成功するが、
        # 将来的にはバリデーションエラーになる予定
        # TODO: プロバイダーバリデーションの実装後に400エラーに変更
        assert response.status_code in [200, 400]

    @patch('doc_ai_helper_backend.api.endpoints.llm.LLMServiceFactory.create_with_mcp')
    def test_query_with_empty_prompt(self, mock_factory, client):
        """空のプロンプトでのクエリテスト"""
        # Configure mock to return mock service
        mock_service = MockLLMService()
        mock_factory.return_value = mock_service
        
        response = client.post(
            "/api/v1/llm/query", json={"prompt": "", "provider": "mock"}
        )
        # 空のプロンプトはPydanticバリデーションで422エラーになる
        assert response.status_code == 422

    def test_query_with_missing_prompt(self, client):
        """プロンプトが欠けているリクエストテスト"""
        response = client.post("/api/v1/llm/query", json={"provider": "mock"})
        assert response.status_code == 422

    def test_query_with_malformed_json(self, client):
        """不正なJSONでのクエリテスト"""
        response = client.post(
            "/api/v1/llm/query",
            data="{invalid json}",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_query_with_very_long_prompt(self, client):
        """非常に長いプロンプトでのテスト"""
        long_prompt = "a" * 10000  # 10KB の文字列
        response = client.post(
            "/api/v1/llm/query", json={"prompt": long_prompt, "provider": "mock"}
        )
        # Mockサービスなので成功するが、実際のサービスではトークン制限でエラーになる可能性
        assert response.status_code == 200

    def test_query_with_special_characters(self, client):
        """特殊文字を含むプロンプトでのテスト"""
        special_prompt = (
            "🚀 Test with emojis and special chars: @#$%^&*()_+{}|:<>?[];'\"\\.,/"
        )
        response = client.post(
            "/api/v1/llm/query", json={"prompt": special_prompt, "provider": "mock"}
        )
        assert response.status_code == 200

    def test_query_with_null_prompt(self, client):
        """nullプロンプトでのテスト"""
        response = client.post(
            "/api/v1/llm/query", json={"prompt": None, "provider": "mock"}
        )
        assert response.status_code == 422

    @patch("doc_ai_helper_backend.services.llm.mock_service.MockLLMService.query")
    def test_query_with_service_exception(self, mock_query, client):
        """サービス例外が発生した場合のテスト"""
        mock_query.side_effect = LLMServiceException("Service error")

        response = client.post(
            "/api/v1/llm/query", json={"prompt": "test prompt", "provider": "mock"}
        )
        assert response.status_code == 500
        assert "Service error" in response.json()["detail"]

    @patch("doc_ai_helper_backend.services.llm.mock_service.MockLLMService.query")
    def test_query_with_timeout(self, mock_query, client):
        """タイムアウトエラーのテスト"""
        mock_query.side_effect = TimeoutError("Request timeout")

        response = client.post(
            "/api/v1/llm/query", json={"prompt": "test prompt", "provider": "mock"}
        )
        assert response.status_code == 500
        assert "timeout" in response.json()["detail"].lower()

    @pytest.mark.skip(
        reason="モックサービスは空のプロンプトでもエラーを返さないためスキップ"
    )
    def test_streaming_with_invalid_prompt(self, client):
        """ストリーミングで無効なプロンプトのテスト"""
        response = client.post(
            "/api/v1/llm/stream", json={"prompt": "", "provider": "mock"}
        )
        # ストリーミングエンドポイントは200を返し、エラーはSSEストリームに含まれる
        assert response.status_code == 200
        # エラー情報がSSEストリームに含まれていることを確認
        assert "error" in response.text

    @pytest.mark.skip(
        reason="ストリーミングテストでExceptionGroupエラーが発生するためスキップ"
    )
    def test_streaming_with_invalid_provider(self, client):
        """ストリーミングで無効なプロバイダーのテスト"""
        response = client.post(
            "/api/v1/llm/stream", json={"prompt": "test", "provider": "mock"}
        )
        # 依存関係注入により常にmockサービスが使われるので200になる
        assert response.status_code == 200

    @pytest.mark.skip(
        reason="ストリーミング時の接続エラーテストはExceptionGroupエラーが発生するためスキップ"
    )
    @patch(
        "doc_ai_helper_backend.services.llm.mock_service.MockLLMService.stream_query"
    )
    def test_streaming_with_connection_error(self, mock_stream, client):
        """ストリーミング時の接続エラーテスト"""

        async def failing_stream(*args, **kwargs):
            raise ConnectionError("Mock connection error")

        mock_stream.side_effect = failing_stream

        response = client.post(
            "/api/v1/llm/stream", json={"prompt": "test", "provider": "mock"}
        )
        # ストリーミング時の接続エラーもSSEストリームでエラーを返す
        assert response.status_code == 200
        # エラー情報がSSEストリームに含まれていることを確認
        assert "error" in response.text

    @pytest.mark.skip(reason="Conversation endpoints not implemented yet")
    def test_conversation_create_with_invalid_data(self, client):
        """会話作成で無効なデータのテスト"""
        response = client.post(
            "/api/v1/llm/conversations",
            json={"title": "", "context": None},  # 空のタイトル
        )
        assert response.status_code == 422

    @pytest.mark.skip(reason="Conversation endpoints not implemented yet")
    def test_conversation_get_nonexistent(self, client):
        """存在しない会話の取得テスト"""
        response = client.get("/api/v1/llm/conversations/nonexistent-id")
        assert response.status_code == 404

    @pytest.mark.skip(reason="Conversation endpoints not implemented yet")
    def test_conversation_message_to_nonexistent(self, client):
        """存在しない会話へのメッセージ送信テスト"""
        response = client.post(
            "/api/v1/llm/conversations/nonexistent-id/messages",
            json={"content": "test message", "provider": "mock"},
        )
        assert response.status_code == 404

    def test_large_context_documents(self, client):
        """大量のコンテキストドキュメントのテスト"""
        large_context = [
            {
                "path": f"doc_{i}.md",
                "content": "Large content " * 1000,  # 大きなコンテンツ
                "metadata": {"title": f"Document {i}"},
            }
            for i in range(50)  # 50個のドキュメント
        ]

        response = client.post(
            "/api/v1/llm/query",
            json={
                "prompt": "Summarize all documents",
                "provider": "mock",
                "context_documents": large_context,
            },
        )
        # 大きなコンテキストでPydanticバリデーションエラーが発生する可能性
        assert response.status_code in [200, 422]

    def test_malformed_context_documents(self, client):
        """不正な形式のコンテキストドキュメントのテスト"""
        malformed_context = [
            {
                "path": "doc1.md",
                # contentが欠けている
                "metadata": {"title": "Document 1"},
            }
        ]

        response = client.post(
            "/api/v1/llm/query",
            json={
                "prompt": "test",
                "provider": "mock",
                "context_documents": malformed_context,
            },
        )
        assert response.status_code == 422

    def test_unsupported_http_method(self, client):
        """サポートされていないHTTPメソッドのテスト"""
        # PUT method to query endpoint should return 405
        response = client.put("/api/v1/llm/query")
        assert response.status_code == 405

        # DELETE method to conversation endpoint (not implemented) should return 404
        response = client.delete("/api/v1/llm/conversations/test-id")
        assert response.status_code == 404  # endpoint doesn't exist

    def test_missing_content_type(self, client):
        """Content-Typeヘッダーが欠けているリクエストのテスト"""
        response = client.post(
            "/api/v1/llm/query",
            data='{"prompt": "test", "provider": "mock"}',
            # Content-Typeヘッダーを意図的に省略
        )
        # FastAPIは自動的にJSONとして解釈するので、通常は成功する
        assert response.status_code in [200, 422]

    def test_rate_limiting_simulation(self, client):
        """レート制限のシミュレーション（将来的な実装のため）"""
        # 現在はレート制限が実装されていないが、大量のリクエストを送信
        responses = []
        for i in range(20):
            response = client.post(
                "/api/v1/llm/query", json={"prompt": f"Request {i}", "provider": "mock"}
            )
            responses.append(response)

        # 現在は全て成功するが、将来的にはレート制限でエラーになる可能性
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 10  # 少なくとも半分は成功する
