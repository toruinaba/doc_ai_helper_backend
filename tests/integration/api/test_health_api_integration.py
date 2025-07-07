"""
Health API 統合テスト

ヘルスチェックエンドポイントの統合をテストします。
"""

import pytest
from fastapi.testclient import TestClient

from doc_ai_helper_backend.main import app


@pytest.mark.integration
@pytest.mark.api
class TestHealthAPIIntegration:
    """Health API統合テストクラス。"""

    @pytest.fixture
    def client(self):
        """テストクライアントを取得する"""
        return TestClient(app)

    def test_health_check_integration(self, client):
        """ヘルスチェックエンドポイントの統合テスト"""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        # ヘルスチェックレスポンスの検証
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_health_check_response_format(self, client):
        """ヘルスチェックレスポンス形式の検証"""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()

        # 必須フィールドの存在確認
        required_fields = ["status", "timestamp", "version"]
        for field in required_fields:
            assert (
                field in data
            ), f"Required field '{field}' missing from health response"

    def test_health_check_performance(self, client):
        """ヘルスチェックのパフォーマンステスト"""
        import time

        start_time = time.time()
        response = client.get("/api/v1/health")
        end_time = time.time()

        assert response.status_code == 200

        # ヘルスチェックは1秒以内に完了すべき
        response_time = end_time - start_time
        assert (
            response_time < 1.0
        ), f"Health check took {response_time:.2f}s, should be < 1.0s"
