"""
LLM API endpoint integration tests.

This module contains integration tests for LLM API endpoints to verify
conversation history handling and optimization.
"""

import os
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
import json

from doc_ai_helper_backend.main import app
from doc_ai_helper_backend.models.llm import MessageItem, MessageRole


class TestLLMAPIIntegration:
    """LLM API エンドポイントの統合テスト"""

    @pytest.mark.asyncio
    async def test_api_conversation_history_basic(self):
        """APIを通じた基本的な会話履歴の処理を確認"""
        # 会話履歴を含むリクエストデータ
        request_data = {
            "prompt": "今日の天気はどうですか？",
            "conversation_history": [
                {"role": "user", "content": "こんにちは"},
                {
                    "role": "assistant",
                    "content": "こんにちは！何かお手伝いできることはありますか？",
                },
            ],
            "provider": "mock",  # 統合テストではモックプロバイダーを使用
            "options": {"temperature": 0.7},
        }

        # ASGIトランスポートを使用してAsyncClientを作成
        import httpx

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as async_client:
            # APIリクエストを送信
            response = await async_client.post("/api/v1/llm/query", json=request_data)

            # レスポンスのステータスコードを確認
            assert response.status_code == 200

            # レスポンスのJSONデータを取得
            response_data = response.json()

            # 必要なフィールドが含まれていることを確認
            assert "content" in response_data
            assert "model" in response_data
            assert "provider" in response_data
            assert "usage" in response_data
            assert "optimized_conversation_history" in response_data
            assert "history_optimization_info" in response_data

            # 最適化された会話履歴が適切に返されることを確認
            assert response_data["optimized_conversation_history"] is not None
            assert isinstance(response_data["optimized_conversation_history"], list)
            assert len(response_data["optimized_conversation_history"]) >= len(
                request_data["conversation_history"]
            )

            # 最適化情報が含まれていることを確認
            assert response_data["history_optimization_info"] is not None
            assert "was_optimized" in response_data["history_optimization_info"]
        assert response_data["optimized_conversation_history"] is not None
        assert isinstance(response_data["optimized_conversation_history"], list)
        assert len(response_data["optimized_conversation_history"]) >= len(
            request_data["conversation_history"]
        )

        # 最適化情報が含まれていることを確認
        assert response_data["history_optimization_info"] is not None
        assert "was_optimized" in response_data["history_optimization_info"]

    def test_api_conversation_history_optimization(self):
        """APIを通じた長い会話履歴の最適化を確認"""
        # 長い会話履歴を作成（要約が発生するように十分長くする）
        conversation_history = []
        # 100往復の非常に長い会話を作成してトークン数を確実に4000を超えるようにする
        for i in range(100):
            conversation_history.extend(
                [
                    {
                        "role": "user",
                        "content": f"質問{i+1}: これは{i+1}番目の非常に長い質問です。トークン数を大幅に増やすために、この文章を非常に長くしています。具体的には、日常生活について、仕事について、趣味について、将来の計画について、家族について、友人について、健康について、旅行について、読書について、映画について、音楽について、スポーツについて、料理について、学習について、キャリアについて、投資について、技術について、ニュースについて、環境について、政治について、文化について、芸術について、科学について、歴史について、哲学について、宗教について、心理学について、社会学について、経済学について等々、様々なトピックについて詳細に質問したいと思います。この質問は意図的に非常に長くしてトークン数を増やしています。",
                    },
                    {
                        "role": "assistant",
                        "content": f"回答{i+1}: ご質問ありがとうございます。{i+1}番目のご質問にお答えします。詳細な説明をさせていただきますと、このような内容になります。日常生活、仕事、趣味、将来の計画、家族、友人、健康、旅行、読書、映画、音楽、スポーツ、料理、学習、キャリア、投資、技術、ニュース、環境、政治、文化、芸術、科学、歴史、哲学、宗教、心理学、社会学、経済学など、どのトピックについても丁寧にお答えできます。この回答も意図的に長くしてトークン数を増やし、確実に最適化が発生するようにしています。各トピックについて詳しく説明することで、より具体的で有用な情報を提供できます。",
                    },
                ]
            )

        request_data = {
            "prompt": "この会話をまとめてください。",
            "conversation_history": conversation_history,
            "provider": "mock",  # モックプロバイダーを使用
            "options": {"temperature": 0.7},
        }

        # APIリクエストを送信
        with TestClient(app) as client:
            response = client.post("/api/v1/llm/query", json=request_data)

        # レスポンスのステータスコードを確認
        assert response.status_code == 200

        # レスポンスのJSONデータを取得
        response_data = response.json()

        # 最適化された会話履歴が返されることを確認
        assert "optimized_conversation_history" in response_data
        assert response_data["optimized_conversation_history"] is not None

        # 最適化情報が含まれていることを確認
        assert "history_optimization_info" in response_data
        assert response_data["history_optimization_info"] is not None

        # デバッグ: 実際の最適化情報の内容を出力
        print(
            f"DEBUG: history_optimization_info = {response_data['history_optimization_info']}"
        )

        # 最適化により会話履歴が短縮されていることを確認
        original_count = len(conversation_history)
        optimized_count = len(response_data["optimized_conversation_history"])

        print(
            f"DEBUG: original_count = {original_count}, optimized_count = {optimized_count}"
        )

        # モックプロバイダーでは必ず最適化が発生する設定
        assert (
            optimized_count < original_count
        ), f"Expected optimization: {optimized_count} < {original_count}"
        assert response_data["history_optimization_info"]["was_optimized"] == True

    def test_api_conversation_history_with_system_message(self):
        """APIを通じたシステムメッセージ付き会話履歴の処理を確認"""
        request_data = {
            "prompt": "前回の話の続きをお願いします。",
            "conversation_history": [
                {
                    "role": "system",
                    "content": "あなたは親切なアシスタントです。常に丁寧に回答してください。",
                },
                {
                    "role": "user",
                    "content": "プロジェクトの進捗について相談があります。",
                },
                {
                    "role": "assistant",
                    "content": "プロジェクトの進捗についてご相談いただき、ありがとうございます。どのような点についてお聞かせください？",
                },
            ],
            "provider": "mock",
            "options": {"temperature": 0.7},
        }

        # APIリクエストを送信
        with TestClient(app) as client:
            response = client.post("/api/v1/llm/query", json=request_data)

        # レスポンスのステータスコードを確認
        assert response.status_code == 200

        # レスポンスのJSONデータを取得
        response_data = response.json()

        # 最適化された会話履歴が返されることを確認
        assert "optimized_conversation_history" in response_data
        assert response_data["optimized_conversation_history"] is not None

        # システムメッセージが保持されていることを確認
        optimized_history = response_data["optimized_conversation_history"]
        system_messages = [msg for msg in optimized_history if msg["role"] == "system"]
        assert len(system_messages) > 0, "System message should be preserved"
        assert (
            system_messages[0]["content"]
            == "あなたは親切なアシスタントです。常に丁寧に回答してください。"
        )

    def test_api_conversation_history_empty(self):
        """APIを通じた空の会話履歴の処理を確認"""
        request_data = {
            "prompt": "初回の質問です。",
            "conversation_history": [],
            "provider": "mock",
            "options": {"temperature": 0.7},
        }

        # APIリクエストを送信
        with TestClient(app) as client:
            response = client.post("/api/v1/llm/query", json=request_data)

        # レスポンスのステータスコードを確認
        assert response.status_code == 200

        # レスポンスのJSONデータを取得
        response_data = response.json()

        # 最適化された会話履歴が返されることを確認（空の場合でも空のリストが返される）
        assert "optimized_conversation_history" in response_data
        assert response_data["optimized_conversation_history"] is not None
        assert isinstance(response_data["optimized_conversation_history"], list)

    def test_api_conversation_history_none(self):
        """APIを通じたNoneの会話履歴の処理を確認"""
        request_data = {
            "prompt": "初回の質問です。",
            "provider": "mock",
            "options": {"temperature": 0.7},
            # conversation_historyを意図的に含めない
        }

        # APIリクエストを送信
        with TestClient(app) as client:
            response = client.post("/api/v1/llm/query", json=request_data)

        # レスポンスのステータスコードを確認
        assert response.status_code == 200

        # レスポンスのJSONデータを取得
        response_data = response.json()

        # 最適化された会話履歴が返されることを確認（Noneの場合でも空のリストが返される）
        assert "optimized_conversation_history" in response_data
        assert response_data["optimized_conversation_history"] is not None
        assert isinstance(response_data["optimized_conversation_history"], list)
        assert len(response_data["optimized_conversation_history"]) == 0

    @pytest.mark.skip(reason="Streaming test requires complex async setup")
    def test_api_stream_conversation_history(self):
        """APIを通じたストリーミングでの会話履歴の処理を確認"""
        # Note: ストリーミングAPIは現在optimized_conversation_historyを返さない
        # 将来の拡張として実装可能
        pass
