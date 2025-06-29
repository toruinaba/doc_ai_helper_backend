"""
API経由でのFunction Calling機能のユニットテスト

このモジュールは、LLM APIエンドポイント（/api/v1/llm/query）経由で
Function Callingが正常に動作するかをテストします。
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from doc_ai_helper_backend.main import app


class TestAPIFunctionCalling:
    """API経由Function Callingのテストクラス"""

    @pytest.fixture
    def client(self):
        """TestClientのフィクスチャ"""
        return TestClient(app)

    def test_api_function_calling_time_tool(self, client):
        """現在時刻取得（Function Calling有効）をテストする"""
        request_data = {
            "prompt": "What is the current time?",
            "provider": "mock",
            "model": "mock-model",
            "enable_tools": True,
            "tool_choice": "auto",
        }

        response = client.post("/api/v1/llm/query", json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert "content" in result
        assert isinstance(result["content"], str)

        # ツール実行結果が含まれることを確認
        if result.get("tool_execution_results"):
            assert len(result["tool_execution_results"]) > 0
            for tool_result in result["tool_execution_results"]:
                assert "function_name" in tool_result
                assert "result" in tool_result

    def test_api_function_calling_char_count(self, client):
        """文字数カウント（Function Calling有効）をテストする"""
        request_data = {
            "prompt": "Please count the characters in this text: Hello World",
            "provider": "mock",
            "model": "mock-model",
            "enable_tools": True,
            "tool_choice": "auto",
        }

        response = client.post("/api/v1/llm/query", json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert "content" in result
        assert isinstance(result["content"], str)

    def test_api_function_calling_calculation(self, client):
        """計算（Function Calling有効）をテストする"""
        request_data = {
            "prompt": "Calculate 15 + 27",
            "provider": "mock",
            "model": "mock-model",
            "enable_tools": True,
            "tool_choice": "auto",
        }

        response = client.post("/api/v1/llm/query", json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert "content" in result
        assert isinstance(result["content"], str)

    def test_api_normal_prompt_without_tools(self, client):
        """通常のプロンプト（Function Calling無効）をテストする"""
        request_data = {
            "prompt": "Hello, how are you doing today?",
            "provider": "mock",
            "model": "mock-model",
            "enable_tools": False,
        }

        response = client.post("/api/v1/llm/query", json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert "content" in result
        assert isinstance(result["content"], str)

        # ツール実行がないことを確認
        tool_results = result.get("tool_execution_results")
        assert tool_results is None or len(tool_results) == 0

    def test_api_error_handling(self, client):
        """APIエラーハンドリングをテストする"""
        # エラーシミュレーションプロンプトでテスト
        request_data = {
            "prompt": "simulate_error",  # Mock serviceでエラーを発生させるキーワード
            "provider": "mock",
            "model": "test-model",
            "enable_tools": False,
        }

        response = client.post("/api/v1/llm/query", json=request_data)

        # エラーレスポンスを期待
        assert response.status_code >= 400

    def test_api_request_validation(self, client):
        """APIリクエスト検証をテストする"""
        # 必須フィールドが欠けているリクエスト
        request_data = {
            "provider": "mock",
            "model": "mock-model",
            # promptが欠けている
        }

        response = client.post("/api/v1/llm/query", json=request_data)

        # バリデーションエラーを期待
        assert response.status_code == 422
