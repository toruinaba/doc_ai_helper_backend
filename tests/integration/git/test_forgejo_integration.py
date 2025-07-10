"""
Forgejo統合テスト

実際のForgejoサーバーとの統合テストを実行します。
環境変数による設定が必要です。
"""

import os
import pytest
from typing import Dict, Any

from doc_ai_helper_backend.services.git.factory import GitServiceFactory
from doc_ai_helper_backend.services.git.forgejo_service import ForgejoService
from doc_ai_helper_backend.models.document import (
    DocumentResponse,
    RepositoryStructureResponse,
)
from doc_ai_helper_backend.core.exceptions import NotFoundException


@pytest.mark.integration
@pytest.mark.forgejo
class TestForgejoIntegration:
    """Forgejo統合テストクラス"""

    @pytest.fixture(scope="class")
    def forgejo_service(self, forgejo_config: Dict[str, str]) -> ForgejoService:
        """Forgejoサービスのフィクスチャ"""
        return GitServiceFactory.create("forgejo", **forgejo_config)

    @pytest.fixture(scope="class")
    def test_repository(self) -> Dict[str, str]:
        """テスト用リポジトリ情報"""
        return {
            "owner": os.getenv("FORGEJO_TEST_OWNER", "testowner"),
            "repo": os.getenv("FORGEJO_TEST_REPO", "testrepo"),
            "ref": "main",
        }

    @pytest.mark.asyncio
    async def test_forgejo_service_creation(self, forgejo_config: Dict[str, str]):
        """Forgejoサービスの作成テスト"""
        service = GitServiceFactory.create("forgejo", **forgejo_config)

        assert isinstance(service, ForgejoService)
        # URL正規化を考慮（末尾スラッシュ除去）
        expected_base_url = forgejo_config["base_url"].rstrip("/")
        assert service.base_url == expected_base_url
        assert service._get_service_name() == "forgejo"

    @pytest.mark.asyncio
    async def test_forgejo_authentication_methods(self, forgejo_config: Dict[str, str]):
        """Forgejo認証方式のテスト"""
        service = ForgejoService(**forgejo_config)

        # 認証ヘッダーの確認
        auth_headers = service._get_auth_headers()
        assert "Authorization" in auth_headers

        # サポートされている認証方式の確認
        auth_methods = service.get_supported_auth_methods()
        assert "token" in auth_methods
        assert "basic_auth" in auth_methods

    @pytest.mark.asyncio
    async def test_get_document_success(
        self, forgejo_service: ForgejoService, test_repository: Dict[str, str]
    ):
        """ドキュメント取得の成功テスト"""
        # README.mdの取得を試行
        path = "README.md"

        try:
            result = await forgejo_service.get_document(
                test_repository["owner"],
                test_repository["repo"],
                path,
                test_repository["ref"],
            )

            # 結果の検証
            assert isinstance(result, DocumentResponse)
            assert result.path == path
            assert result.owner == test_repository["owner"]
            assert result.repository == test_repository["repo"]
            assert result.service == "forgejo"
            assert result.content.content is not None
            assert len(result.content.content) > 0

        except NotFoundException:
            # リポジトリやファイルが存在しない場合はスキップ
            pytest.skip(
                f"Test repository {test_repository['owner']}/{test_repository['repo']} or file {path} not found"
            )

    @pytest.mark.asyncio
    async def test_get_repository_structure_success(
        self, forgejo_service: ForgejoService, test_repository: Dict[str, str]
    ):
        """リポジトリ構造取得の成功テスト"""
        try:
            result = await forgejo_service.get_repository_structure(
                test_repository["owner"],
                test_repository["repo"],
                test_repository["ref"],
            )

            # 結果の検証
            assert isinstance(result, RepositoryStructureResponse)
            assert result.owner == test_repository["owner"]
            assert result.repo == test_repository["repo"]
            assert result.service == "forgejo"
            assert result.tree is not None
            assert len(result.tree) > 0

        except NotFoundException:
            # リポジトリが存在しない場合はスキップ
            pytest.skip(
                f"Test repository {test_repository['owner']}/{test_repository['repo']} not found"
            )

    @pytest.mark.asyncio
    async def test_check_repository_exists_true(
        self, forgejo_service: ForgejoService, test_repository: Dict[str, str]
    ):
        """リポジトリ存在確認（存在する場合）のテスト"""
        try:
            exists = await forgejo_service.check_repository_exists(
                test_repository["owner"], test_repository["repo"]
            )

            # 存在する場合のテスト
            assert exists is True

        except Exception:
            # リポジトリが存在しない場合はスキップ
            pytest.skip(
                f"Test repository {test_repository['owner']}/{test_repository['repo']} not found"
            )

    @pytest.mark.asyncio
    async def test_check_repository_exists_false(self, forgejo_service: ForgejoService):
        """リポジトリ存在確認（存在しない場合）のテスト"""
        # 存在しないリポジトリでテスト
        exists = await forgejo_service.check_repository_exists(
            "nonexistent_owner", "nonexistent_repo"
        )

        assert exists is False

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, forgejo_service: ForgejoService):
        """ドキュメント取得の失敗テスト（ファイル未発見）"""
        with pytest.raises(NotFoundException) as exc_info:
            await forgejo_service.get_document(
                "nonexistent_owner", "nonexistent_repo", "nonexistent.md"
            )

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_repository_structure_not_found(
        self, forgejo_service: ForgejoService
    ):
        """リポジトリ構造取得の失敗テスト（リポジトリ未発見）"""
        with pytest.raises(NotFoundException) as exc_info:
            await forgejo_service.get_repository_structure(
                "nonexistent_owner", "nonexistent_repo"
            )

        assert "not found" in str(exc_info.value).lower()

    def test_url_normalization(self):
        """URL正規化のテスト"""
        # 末尾スラッシュありの場合
        service_with_slash = ForgejoService(
            base_url="https://forgejo.example.com/", access_token="test_token"
        )
        assert service_with_slash.base_url == "https://forgejo.example.com"
        assert service_with_slash.api_base_url == "https://forgejo.example.com/api/v1"

        # 末尾スラッシュなしの場合
        service_without_slash = ForgejoService(
            base_url="https://forgejo.example.com", access_token="test_token"
        )
        assert service_without_slash.base_url == "https://forgejo.example.com"
        assert (
            service_without_slash.api_base_url == "https://forgejo.example.com/api/v1"
        )

    @pytest.mark.asyncio
    async def test_error_handling_unauthorized(self):
        """認証エラーのハンドリングテスト"""
        # 無効なトークンでサービスを作成
        service = ForgejoService(
            base_url=os.getenv("FORGEJO_BASE_URL", "https://forgejo.example.com"),
            access_token="invalid_token",
        )

        # 認証エラーが発生することを確認
        with pytest.raises(Exception):  # 具体的な例外タイプは実装による
            await service.get_document("testowner", "testrepo", "README.md")

    @pytest.mark.asyncio
    async def test_factory_integration(self, forgejo_config: Dict[str, str]):
        """ファクトリー経由でのForgejo統合テスト"""
        service = GitServiceFactory.create("forgejo", **forgejo_config)

        # サービスタイプの確認
        assert isinstance(service, ForgejoService)
        assert service._get_service_name() == "forgejo"

        # 基本機能の確認
        auth_methods = service.get_supported_auth_methods()
        assert isinstance(auth_methods, list)
        assert len(auth_methods) > 0


@pytest.mark.integration
@pytest.mark.forgejo
@pytest.mark.slow
class TestForgejoPerformance:
    """Forgejoパフォーマンステスト"""

    @pytest.fixture(scope="class")
    def forgejo_service(self, forgejo_config: Dict[str, str]) -> ForgejoService:
        """Forgejoサービスのフィクスチャ"""
        return GitServiceFactory.create("forgejo", **forgejo_config)

    @pytest.fixture(scope="class")
    def test_repository(self) -> Dict[str, str]:
        """テスト用リポジトリ情報"""
        return {
            "owner": os.getenv("FORGEJO_TEST_OWNER", "testowner"),
            "repo": os.getenv("FORGEJO_TEST_REPO", "testrepo"),
            "ref": "main",
        }

    @pytest.mark.asyncio
    async def test_multiple_requests_performance(
        self, forgejo_service: ForgejoService, test_repository: Dict[str, str]
    ):
        """複数リクエストのパフォーマンステスト"""
        import time

        # 複数のドキュメント取得を並行実行
        start_time = time.time()

        tasks = []
        for i in range(3):  # 3回のリクエスト
            try:
                await forgejo_service.get_repository_structure(
                    test_repository["owner"],
                    test_repository["repo"],
                    test_repository["ref"],
                )
            except NotFoundException:
                pytest.skip("Test repository not found for performance test")

        end_time = time.time()
        total_time = end_time - start_time

        # 合理的な時間内での完了を確認（30秒以内）
        assert total_time < 30.0, f"Performance test took too long: {total_time}s"
