"""
Integration tests for GitHub service using real GitHub API.
"""

import os
import pytest
from datetime import datetime

from doc_ai_helper_backend.core.exceptions import (
    GitServiceException,
    NotFoundException,
    RateLimitException,
    UnauthorizedException,
)
from doc_ai_helper_backend.services.git.github_service import GitHubService


def pytest_configure(config):
    """統合テストの設定"""
    # 必要な環境変数をチェック
    required_env_vars = {
        "GITHUB_TOKEN": "GitHub API integration tests",
    }

    missing_vars = []
    for var, description in required_env_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var} (for {description})")

    if missing_vars:
        pytest.skip(
            f"Integration tests skipped. Missing environment variables: {', '.join(missing_vars)}"
        )


class TestGitHubServiceRealAPI:
    """GitHubService実API統合テスト（実際のGitHubトークンが必要）"""

    @pytest.fixture
    def github_service(self):
        """実際のGitHubServiceのインスタンスを取得する"""
        # 環境変数からアクセストークンを取得
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            pytest.skip("GITHUB_TOKEN environment variable not set")

        return GitHubService(access_token=token)

    @pytest.mark.asyncio
    async def test_get_document(self, github_service):
        """ドキュメント取得のテスト"""
        # 実際の公開リポジトリからドキュメントを取得
        response = await github_service.get_document(
            "microsoft", "vscode", "README.md", "main"
        )

        # 結果を検証
        assert response.path == "README.md"
        assert response.name == "README.md"
        assert response.type.value == "markdown"
        assert response.content.content.startswith("# Visual Studio Code")
        assert response.service == "github"
        assert response.owner == "microsoft"
        assert response.repository == "vscode"
        assert response.ref == "main"

        # メタデータの検証
        assert response.metadata.size > 0
        assert (
            str(response.metadata.html_url)
            == "https://github.com/microsoft/vscode/blob/main/README.md"
        )
        assert (
            str(response.metadata.download_url)
            == "https://raw.githubusercontent.com/microsoft/vscode/main/README.md"
        )

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, github_service):
        """存在しないドキュメント取得のテスト"""
        # 存在しないパスを指定
        with pytest.raises((NotFoundException, GitServiceException)):
            await github_service.get_document(
                "microsoft", "vscode", "nonexistent-file.md", "main"
            )

    @pytest.mark.asyncio
    async def test_get_repository_structure(self, github_service):
        """リポジトリ構造取得のテスト"""
        # 実際の公開リポジトリの構造を取得
        response = await github_service.get_repository_structure(
            "microsoft", "vscode", "main"
        )

        # 結果を検証
        assert response.service == "github"
        assert response.owner == "microsoft"
        assert response.repo == "vscode"
        assert response.ref == "main"

        # ツリーの検証
        assert len(response.tree) > 0

        # READMEファイルの存在確認
        readme = next(
            (item for item in response.tree if item.path == "README.md"), None
        )
        assert readme is not None
        assert readme.type == "file"
        assert readme.name == "README.md"
        assert (
            str(readme.download_url)
            == "https://raw.githubusercontent.com/microsoft/vscode/main/README.md"
        )
        assert (
            str(readme.html_url)
            == "https://github.com/microsoft/vscode/blob/main/README.md"
        )

    @pytest.mark.asyncio
    async def test_get_repository_structure_with_path(self, github_service):
        """特定パス配下のリポジトリ構造取得のテスト"""
        # 実際の公開リポジトリの特定パス配下の構造を取得
        response = await github_service.get_repository_structure(
            "microsoft", "vscode", "main", "src"
        )

        # 結果を検証
        assert response.service == "github"
        assert response.owner == "microsoft"
        assert response.repo == "vscode"

        # パスでフィルタリングされていることを確認
        for item in response.tree:
            assert item.path.startswith("src")

    @pytest.mark.asyncio
    async def test_search_repository(self, github_service):
        """リポジトリ検索のテスト"""
        # 実際の公開リポジトリを検索
        results = await github_service.search_repository(
            "microsoft", "vscode", "main.ts", 5
        )

        # 結果を検証
        assert len(results) > 0
        assert len(results) <= 5

        # 検索結果の検証
        for result in results:
            assert "path" in result
            assert "name" in result
            assert "html_url" in result
            assert "repository" in result
            assert result["repository"]["name"] == "vscode"
            assert result["repository"]["owner"] == "microsoft"

    @pytest.mark.asyncio
    async def test_check_repository_exists_true(self, github_service):
        """リポジトリ存在確認のテスト（存在する場合）"""
        # 実際の公開リポジトリの存在を確認
        result = await github_service.check_repository_exists("microsoft", "vscode")

        # 結果を検証
        assert result is True

    @pytest.mark.asyncio
    async def test_check_repository_exists_false(self, github_service):
        """リポジトリ存在確認のテスト（存在しない場合）"""
        with pytest.raises((NotFoundException, GitServiceException)):
            response = await github_service.check_repository_exists(
                "microsoft", "nonexistent-repo-12345"
            )
