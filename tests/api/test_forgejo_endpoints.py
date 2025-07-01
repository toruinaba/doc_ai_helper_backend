"""
Forgejoサービス用APIエンドポイントの統合テスト
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from doc_ai_helper_backend.main import app
from doc_ai_helper_backend.models.document import (
    DocumentResponse,
    DocumentContent,
    DocumentMetadata,
    DocumentType,
    RepositoryStructureResponse,
    FileTreeItem,
)
from doc_ai_helper_backend.core.config import settings
from datetime import datetime


class TestForgejoAPIEndpoints:
    """ForgejoサービスのAPIエンドポイントテストクラス"""

    @pytest.fixture
    def client(self):
        """テストクライアントを作成"""
        return TestClient(app)

    @pytest.fixture
    def mock_document_response(self):
        """モックドキュメントレスポンスを作成"""
        return DocumentResponse(
            path="README.md",
            name="README.md",
            type=DocumentType.MARKDOWN,
            content=DocumentContent(
                content="# Test Document\n\nThis is a test document.",
                encoding="utf-8",
            ),
            metadata=DocumentMetadata(
                size=42,
                last_modified=datetime.now(),
                content_type="text/markdown",
                sha="abc123",
                download_url=None,
                html_url=None,
                raw_url=None,
                extra={},
            ),
            repository="test-repo",
            owner="test-owner",
            service="forgejo",
            ref="main",
            links=[],
            transformed_content="# Test Document\n\nThis is a test document.",
        )

    @pytest.fixture
    def mock_structure_response(self):
        """モック構造レスポンスを作成"""
        return RepositoryStructureResponse(
            repo="test-repo",
            owner="test-owner",
            service="forgejo",
            ref="main",
            tree=[
                FileTreeItem(
                    path="README.md",
                    type="file",
                    name="README.md",
                    size=42,
                    sha="abc123",
                    download_url=None,
                    html_url=None,
                    git_url=None,
                ),
                FileTreeItem(
                    path="src/",
                    type="directory",
                    name="src",
                    size=None,
                    sha=None,
                    download_url=None,
                    html_url=None,
                    git_url=None,
                ),
            ],
            last_updated=datetime.now(),
        )

    @patch(
        "doc_ai_helper_backend.services.document_service.DocumentService.get_document"
    )
    def test_get_document_forgejo(
        self, mock_get_document, client, mock_document_response
    ):
        """Forgejoサービスでドキュメント取得をテスト"""
        # モック設定
        mock_get_document.return_value = mock_document_response

        # APIリクエスト
        response = client.get(
            f"{settings.api_prefix}/documents/contents/forgejo/test-owner/test-repo/README.md?ref=main"
        )

        # レスポンス検証
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "forgejo"
        assert data["owner"] == "test-owner"
        assert data["repository"] == "test-repo"
        assert data["path"] == "README.md"
        assert data["ref"] == "main"
        assert data["type"] == "markdown"

        # サービスメソッドが正しい引数で呼ばれたことを確認
        mock_get_document.assert_called_once_with(
            "forgejo",
            "test-owner",
            "test-repo",
            "README.md",
            "main",
            transform_links=True,
            base_url=None,
        )

    @patch(
        "doc_ai_helper_backend.services.document_service.DocumentService.get_repository_structure"
    )
    def test_get_repository_structure_forgejo(
        self, mock_get_structure, client, mock_structure_response
    ):
        """Forgejoサービスでリポジトリ構造取得をテスト"""
        # モック設定
        mock_get_structure.return_value = mock_structure_response

        # APIリクエスト
        response = client.get(
            f"{settings.api_prefix}/documents/structure/forgejo/test-owner/test-repo?ref=main"
        )

        # レスポンス検証
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "forgejo"
        assert data["owner"] == "test-owner"
        assert data["repo"] == "test-repo"
        assert data["ref"] == "main"
        assert len(data["tree"]) == 2

        # サービスメソッドが正しい引数で呼ばれたことを確認
        mock_get_structure.assert_called_once_with(
            "forgejo", "test-owner", "test-repo", "main", ""
        )

    def test_invalid_service_name(self, client):
        """無効なサービス名のテスト"""
        response = client.get(
            f"{settings.api_prefix}/documents/contents/invalid-service/test-owner/test-repo/README.md"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Unsupported Git service" in data.get("message", data.get("detail", ""))

    def test_get_document_with_parameters(self, client):
        """パラメータ付きドキュメント取得のテスト"""
        with patch(
            "doc_ai_helper_backend.services.document_service.DocumentService.get_document"
        ) as mock_get_document:
            mock_get_document.return_value = DocumentResponse(
                path="test.md",
                name="test.md",
                type=DocumentType.MARKDOWN,
                content=DocumentContent(content="# Test", encoding="utf-8"),
                metadata=DocumentMetadata(
                    size=6,
                    last_modified=datetime.now(),
                    content_type="text/markdown",
                    sha="def456",
                    download_url=None,
                    html_url=None,
                    raw_url=None,
                    extra={},
                ),
                repository="test-repo",
                owner="test-owner",
                service="forgejo",
                ref="develop",
                links=[],
                transformed_content="# Test",
            )

            # パラメータ付きでAPIリクエスト
            response = client.get(
                f"{settings.api_prefix}/documents/contents/forgejo/test-owner/test-repo/test.md"
                "?ref=develop&transform_links=false&base_url=https://example.com"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["ref"] == "develop"

            # サービスメソッドが正しい引数で呼ばれたことを確認
            mock_get_document.assert_called_once_with(
                "forgejo",
                "test-owner",
                "test-repo",
                "test.md",
                "develop",
                transform_links=False,
                base_url="https://example.com",
            )

    def test_get_structure_with_path_filter(self, client):
        """パス フィルター付き構造取得のテスト"""
        with patch(
            "doc_ai_helper_backend.services.document_service.DocumentService.get_repository_structure"
        ) as mock_get_structure:
            mock_get_structure.return_value = RepositoryStructureResponse(
                repo="test-repo",
                owner="test-owner",
                service="forgejo",
                ref="main",
                tree=[],
                last_updated=datetime.now(),
            )

            # パス フィルター付きでAPIリクエスト
            response = client.get(
                f"{settings.api_prefix}/documents/structure/forgejo/test-owner/test-repo"
                "?ref=main&path=src/"
            )

            assert response.status_code == 200

            # サービスメソッドが正しい引数で呼ばれたことを確認
            mock_get_structure.assert_called_once_with(
                "forgejo", "test-owner", "test-repo", "main", "src/"
            )

    @patch(
        "doc_ai_helper_backend.services.document_service.DocumentService.get_document"
    )
    def test_service_error_handling(self, mock_get_document, client):
        """サービスエラーのハンドリングテスト"""
        from doc_ai_helper_backend.core.exceptions import GitServiceException

        # サービスでエラーが発生する場合をモック
        mock_get_document.side_effect = GitServiceException("Connection failed")

        response = client.get(
            f"{settings.api_prefix}/documents/contents/forgejo/test-owner/test-repo/README.md"
        )

        # GitServiceExceptionは500としてマッピングされる
        assert response.status_code == 500
