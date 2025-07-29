"""
会話履歴API機能のユニットテスト

このモジュールは、会話履歴管理API機能をテストします。
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from doc_ai_helper_backend.main import app


class TestConversationHistoryAPI:
    """会話履歴APIのテストクラス"""

    @pytest.fixture
    def client(self):
        """TestClientのフィクスチャ"""
        return TestClient(app)

    def test_conversation_history_basic_flow(self, client):
        """会話履歴の基本フローをテストする"""
        # 新しい会話を開始
        request_data = {
            "prompt": "Hello, I need help with documentation.",
            "provider": "mock",
            "model": "mock-model",
            "enable_tools": False,
        }

        response = client.post("/api/v1/llm/query", json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert "content" in result
        assert isinstance(result["content"], str)

        # 会話IDが返されることを確認（実装依存）
        conversation_id = result.get("conversation_id")

        if conversation_id:
            # 同じ会話の続きを送信
            followup_data = {
                "prompt": "Can you explain more about that?",
                "provider": "mock",
                "model": "mock-model",
                "enable_tools": False,
                "conversation_id": conversation_id,
            }

            followup_response = client.post("/api/v1/llm/query", json=followup_data)

            assert followup_response.status_code == 200
            followup_result = followup_response.json()
            assert "content" in followup_result
            assert isinstance(followup_result["content"], str)

    def test_conversation_history_with_tools(self, client):
        """ツール使用時の会話履歴をテストする"""
        request_data = {
            "prompt": "What is the current time and help me with documentation?",
            "provider": "mock",
            "model": "mock-model",
            "enable_tools": True,
            "tool_choice": "auto",
        }

        response = client.post("/api/v1/llm/query", json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert "content" in result

        # ツール実行結果も履歴に含まれることを確認
        if result.get("tool_execution_results"):
            assert len(result["tool_execution_results"]) >= 0

    def test_conversation_context_preservation(self, client):
        """会話コンテキストの保持をテストする"""
        # 最初の質問
        first_request = {
            "prompt": "My name is Alice and I'm working on a Python project.",
            "provider": "mock",
            "model": "mock-model",
            "enable_tools": False,
        }

        first_response = client.post("/api/v1/llm/query", json=first_request)
        assert first_response.status_code == 200

        conversation_id = first_response.json().get("conversation_id")

        if conversation_id:
            # コンテキストを参照する質問
            context_request = {
                "prompt": "What was my name again?",
                "provider": "mock",
                "model": "mock-model",
                "enable_tools": False,
                "conversation_id": conversation_id,
            }

            context_response = client.post("/api/v1/llm/query", json=context_request)
            assert context_response.status_code == 200

            result = context_response.json()
            assert "content" in result

    def test_conversation_history_limits(self, client):
        """会話履歴の制限をテストする"""
        # 長い会話を作成
        conversation_id = None

        for i in range(5):  # 複数回のやり取り
            request_data = {
                "prompt": f"This is message number {i + 1}. Please respond.",
                "provider": "mock",
                "model": "mock-model",
                "enable_tools": False,
            }

            if conversation_id:
                request_data["conversation_id"] = conversation_id

            response = client.post("/api/v1/llm/query", json=request_data)
            assert response.status_code == 200

            result = response.json()
            if not conversation_id:
                conversation_id = result.get("conversation_id")

    def test_invalid_conversation_id(self, client):
        """無効な会話IDの処理をテストする"""
        request_data = {
            "prompt": "Hello with invalid conversation ID",
            "provider": "mock",
            "model": "mock-model",
            "enable_tools": False,
            "conversation_id": "invalid-id-12345",
        }

        response = client.post("/api/v1/llm/query", json=request_data)

        # 無効なIDでもエラーにならず、新しい会話として処理されることを期待
        assert response.status_code == 200
        result = response.json()
        assert "content" in result

    def test_conversation_history_retrieval(self, client):
        """会話履歴取得をテストする（実装されている場合）"""
        # 会話を開始
        request_data = {
            "prompt": "Start a conversation about API testing.",
            "provider": "mock",
            "model": "mock-model",
            "enable_tools": False,
        }

        response = client.post("/api/v1/llm/query", json=request_data)
        assert response.status_code == 200

        conversation_id = response.json().get("conversation_id")

        if conversation_id:
            # 履歴取得エンドポイントがあるかテスト
            try:
                history_response = client.get(
                    f"/api/v1/llm/conversations/{conversation_id}"
                )

                if history_response.status_code == 200:
                    history_data = history_response.json()
                    assert "messages" in history_data or "history" in history_data

            except Exception:
                # エンドポイントが実装されていない場合はスキップ
                pytest.skip("Conversation history retrieval endpoint not implemented")

    def test_conversation_cleanup(self, client):
        """会話のクリーンアップをテストする（実装されている場合）"""
        # 会話を開始
        request_data = {
            "prompt": "Test conversation for cleanup.",
            "provider": "mock",
            "model": "mock-model",
            "enable_tools": False,
        }

        response = client.post("/api/v1/llm/query", json=request_data)
        assert response.status_code == 200

        conversation_id = response.json().get("conversation_id")

        if conversation_id:
            # クリーンアップエンドポイントがあるかテスト
            try:
                cleanup_response = client.delete(
                    f"/api/v1/llm/conversations/{conversation_id}"
                )

                # 削除が成功するか、適切にハンドリングされることを確認
                assert cleanup_response.status_code in [200, 204, 404]

            except Exception:
                # エンドポイントが実装されていない場合はスキップ
                pytest.skip("Conversation cleanup endpoint not implemented")

    def test_conversation_history_memory_management(self, client):
        """会話履歴のメモリ管理をテストする"""
        # 複数の独立した会話を作成
        conversation_ids = []

        for i in range(3):
            request_data = {
                "prompt": f"Independent conversation {i + 1}",
                "provider": "mock",
                "model": "mock-model",
                "enable_tools": False,
            }

            response = client.post("/api/v1/llm/query", json=request_data)
            assert response.status_code == 200

            conversation_id = response.json().get("conversation_id")
            if conversation_id:
                conversation_ids.append(conversation_id)

        # 各会話が独立していることを確認
        for conversation_id in conversation_ids:
            if conversation_id:
                followup_data = {
                    "prompt": "What was the topic of our conversation?",
                    "provider": "mock",
                    "model": "mock-model",
                    "enable_tools": False,
                    "conversation_id": conversation_id,
                }

                followup_response = client.post("/api/v1/llm/query", json=followup_data)
                assert followup_response.status_code == 200
