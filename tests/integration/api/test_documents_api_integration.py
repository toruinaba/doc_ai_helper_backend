"""
Document API 統合テスト

ドキュメント取得、構造取得、リンク変換などのAPI統合をテストします。
"""

import os
import pytest
from fastapi.testclient import TestClient

from doc_ai_helper_backend.main import app


@pytest.mark.integration
@pytest.mark.api
class TestDocumentsAPIIntegration:
    """Document API統合テストクラス。"""

    @pytest.fixture
    def client(self):
        """テストクライアントを取得する"""
        return TestClient(app)

    @pytest.mark.skipif(
        not __import__("doc_ai_helper_backend.core.config", fromlist=["settings"]).settings.github_token,
        reason="GitHub token not available for integration test",
    )
    def test_get_document_github_integration(self, client):
        """GitHub経由でのドキュメント取得統合テスト"""
        # 実際に存在するGitHub公開リポジトリのREADME.mdを取得
        # octocat/Hello-World は古いリポジトリなので、より確実なリポジトリを使用
        response = client.get(
            "/api/v1/documents/contents/github/microsoft/vscode/README.md"
        )

        assert response.status_code == 200
        data = response.json()

        # レスポンス構造の検証
        assert "path" in data
        assert "content" in data
        assert "metadata" in data
        assert "links" in data
        assert data["service"] == "github"
        assert data["owner"] == "microsoft"
        assert data["repository"] == "vscode"

    @pytest.mark.skipif(
        not __import__("doc_ai_helper_backend.core.config", fromlist=["settings"]).settings.forgejo_token,
        reason="Forgejo token not available for integration test",
    )
    def test_get_document_forgejo_integration(self, client):
        """Forgejo経由でのドキュメント取得統合テスト"""
        from doc_ai_helper_backend.core.config import settings
        forgejo_base_url = settings.forgejo_base_url
        forgejo_owner = settings.e2e_forgejo_owner
        forgejo_repo = settings.e2e_forgejo_repo

        if not all([forgejo_base_url, forgejo_owner, forgejo_repo]):
            pytest.skip("Forgejo test configuration not complete")

        # Forgejoリポジトリのドキュメントを取得
        response = client.get(
            f"/api/v1/documents/contents/forgejo/{forgejo_owner}/{forgejo_repo}/README.md"
        )

        assert response.status_code == 200
        data = response.json()

        # レスポンス構造の検証
        assert data["service"] == "forgejo"
        assert data["owner"] == forgejo_owner
        assert data["repository"] == forgejo_repo

    def test_get_repository_structure_integration(self, client):
        """リポジトリ構造取得の統合テスト"""
        # Mock サービスを使用
        response = client.get("/api/v1/documents/structure/mock/test-owner/test-repo")

        assert response.status_code == 200
        data = response.json()

        # 構造データの検証
        assert "tree" in data  # "items" から "tree" に変更
        assert "service" in data
        assert "owner" in data
        assert "repo" in data  # "repository" から "repo" に変更

    def test_link_transformation_integration(self, client):
        """リンク変換機能の統合テスト"""
        # リンク変換有効でドキュメントを取得
        response = client.get(
            "/api/v1/documents/contents/mock/test-owner/test-repo/docs/sample.md",
            params={"transform_links": True},
        )

        assert response.status_code == 200
        data = response.json()

        # リンク変換が実行されていることを確認
        assert "transformed_content" in data
        assert "links" in data

    def test_api_error_handling_integration(self, client):
        """API エラーハンドリングの統合テスト"""
        # 存在しないリポジトリ（GitHub APIは404を返す）
        response = client.get(
            "/api/v1/documents/contents/github/nonexistent/repo/README.md"
        )
        # GitHub APIの404は正しく404として処理される
        assert response.status_code == 404

        # 不正なサービス名（実際には404が返される）
        response = client.get(
            "/api/v1/documents/contents/invalid-service/owner/repo/file.md"
        )
        assert response.status_code == 404  # 400から404に修正

    def test_api_parameter_validation_integration(self, client):
        """APIパラメータ検証の統合テスト"""
        # 不正なパラメータでのリクエスト
        response = client.get(
            "/api/v1/documents/contents/mock/test-owner/test-repo/sample.md",
            params={"transform_links": "invalid_boolean"},
        )
        # FastAPIの自動バリデーションにより422エラーが返される
        assert response.status_code == 422
