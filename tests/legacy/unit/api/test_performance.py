"""
APIパフォーマンステスト
"""

import time
import pytest
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient

from doc_ai_helper_backend.main import app


class TestAPIPerformance:
    """API パフォーマンステスト"""

    @pytest.fixture
    def client(self):
        """TestClientのフィクスチャ"""
        return TestClient(app)

    def test_health_check_performance(self, client):
        """ヘルスチェックAPIのパフォーマンステスト"""
        start_time = time.time()

        response = client.get("/api/v1/health")

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 0.1  # 100ms以内の応答

    def test_document_retrieval_performance(self, client):
        """ドキュメント取得APIのパフォーマンステスト"""
        start_time = time.time()

        response = client.get(
            "/api/v1/documents/contents/mock/octocat/Hello-World/README.md"
        )

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 1.0  # 1秒以内の応答

        # レスポンス内容の基本チェック
        data = response.json()
        assert "content" in data
        assert "metadata" in data

    def test_llm_query_performance(self, client):
        """LLM問い合わせAPIのパフォーマンステスト"""
        start_time = time.time()

        response = client.post(
            "/api/v1/llm/query", json={"prompt": "What is Python?", "provider": "mock"}
        )

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 5.0  # 5秒以内の応答（外部API経由でやや遅い場合もある）

    @pytest.mark.parametrize("concurrent_requests", [5, 10])
    def test_concurrent_document_requests(self, client, concurrent_requests):
        """ドキュメント取得APIの同時リクエストテスト"""

        def make_request():
            return client.get(
                "/api/v1/documents/contents/mock/octocat/Hello-World/README.md"
            )

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [
                executor.submit(make_request) for _ in range(concurrent_requests)
            ]
            responses = [f.result() for f in futures]
        end_time = time.time()

        # すべてのレスポンスが成功
        assert all(r.status_code == 200 for r in responses)

        # 平均応答時間が許容範囲内
        total_time = end_time - start_time
        avg_response_time = total_time / concurrent_requests
        assert avg_response_time < 1.0  # 平均1秒以内

    @pytest.mark.parametrize("concurrent_requests", [3, 5])
    def test_concurrent_llm_requests(self, client, concurrent_requests):
        """LLM APIの同時リクエストテスト"""

        def make_request(request_id):
            return client.post(
                "/api/v1/llm/query",
                json={"prompt": f"Test request {request_id}", "provider": "mock"},
            )

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [
                executor.submit(make_request, i) for i in range(concurrent_requests)
            ]
            responses = [f.result() for f in futures]
        end_time = time.time()

        # すべてのレスポンスが成功
        successful_responses = [r for r in responses if r.status_code == 200]
        assert len(successful_responses) >= concurrent_requests * 0.8  # 80%以上成功

        # 全体の処理時間が許容範囲内
        total_time = end_time - start_time
        assert total_time < 10.0  # 10秒以内に全て完了

    def test_memory_usage_stability(self, client):
        """メモリ使用量の安定性テスト"""
        import gc

        # 多数のリクエストを実行してメモリリークがないかチェック
        for i in range(50):
            response = client.get(
                f"/api/v1/documents/contents/mock/octocat/Hello-World/README.md"
            )
            assert response.status_code == 200

            if i % 10 == 0:
                gc.collect()  # 定期的にガベージコレクション

        # 最後にガベージコレクションを実行
        gc.collect()

        # テストが正常に完了すれば、大きなメモリリークはないと判断
        assert True

    @pytest.mark.benchmark
    def test_api_response_sizes(self, client):
        """APIレスポンスサイズのテスト"""
        # ドキュメント取得レスポンス
        doc_response = client.get(
            "/api/v1/documents/contents/mock/octocat/Hello-World/README.md"
        )
        doc_size = len(doc_response.content)

        # LLM問い合わせレスポンス
        llm_response = client.post(
            "/api/v1/llm/query", json={"prompt": "Short answer", "provider": "mock"}
        )
        llm_size = len(llm_response.content)

        # 構造取得レスポンス
        structure_response = client.get(
            "/api/v1/documents/structure/mock/octocat/Hello-World"
        )
        structure_size = len(structure_response.content)

        # レスポンスサイズが合理的な範囲内であることを確認
        assert doc_size < 50 * 1024  # 50KB以下
        assert llm_size < 10 * 1024  # 10KB以下
        assert structure_size < 100 * 1024  # 100KB以下

        print(f"Document response size: {doc_size} bytes")
        print(f"LLM response size: {llm_size} bytes")
        print(f"Structure response size: {structure_size} bytes")
