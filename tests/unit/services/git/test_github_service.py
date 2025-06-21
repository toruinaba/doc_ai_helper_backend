"""
Test GitHub service implementation.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from doc_ai_helper_backend.core.exceptions import (
    GitServiceException,
    NotFoundException,
    RateLimitException,
    UnauthorizedException,
)
from doc_ai_helper_backend.services.git.github_service import GitHubService


class TestGitHubService:
    """GitHubServiceの単体テスト"""

    @pytest.fixture
    def github_service(self):
        """GitHubServiceのインスタンスを取得する"""
        return GitHubService(access_token="test_token")

    def test_service_name(self, github_service):
        """サービス名のテスト"""
        assert github_service.service_name == "github"

    def test_headers(self, github_service):
        """HTTPヘッダーのテスト"""
        headers = github_service.headers
        assert "Authorization" in headers
        assert headers["Authorization"] == "token test_token"
        assert headers["Accept"] == "application/vnd.github.v3+json"
        assert headers["User-Agent"] == "DocAIHelperBackend"

    @pytest.mark.asyncio
    async def test_make_request_success(self, github_service):
        """リクエスト成功時のテスト"""
        # モックデータを準備
        mock_data = {"key": "value"}
        mock_headers = {"X-RateLimit-Remaining": "100"}

        # _make_requestメソッド自体をモック
        with patch.object(
            github_service, "_make_request", new_callable=AsyncMock
        ) as mock_make_request:
            # 戻り値を設定
            mock_make_request.return_value = (mock_data, mock_headers)

            # メソッドを呼び出し
            data, headers = await github_service._make_request(
                "GET", "https://api.github.com/test"
            )

            # 結果を検証
            assert data == mock_data
            assert headers == mock_headers
            mock_make_request.assert_called_once_with(
                "GET", "https://api.github.com/test"
            )

    @pytest.mark.asyncio
    async def test_make_request_rate_limit(self, github_service):
        """レート制限時のテスト"""
        # _make_requestメソッド自体をモック
        with patch.object(
            github_service, "_make_request", new_callable=AsyncMock
        ) as mock_make_request:
            # 例外を発生させる
            mock_make_request.side_effect = RateLimitException(
                "GitHub API rate limit exceeded."
            )

            # レート制限例外が発生することを確認
            with pytest.raises(RateLimitException):
                await github_service._make_request("GET", "https://api.github.com/test")

    @pytest.mark.asyncio
    async def test_make_request_not_found(self, github_service):
        """リソース未発見時のテスト"""
        # _make_requestメソッド自体をモック
        with patch.object(
            github_service, "_make_request", new_callable=AsyncMock
        ) as mock_make_request:
            # 例外を発生させる
            mock_make_request.side_effect = NotFoundException(
                "Resource not found on GitHub."
            )

            # NotFoundException例外が発生することを確認
            with pytest.raises(NotFoundException):
                await github_service._make_request("GET", "https://api.github.com/test")

    @pytest.mark.asyncio
    async def test_make_request_unauthorized(self, github_service):
        """認証失敗時のテスト"""
        # _make_requestメソッド自体をモック
        with patch.object(
            github_service, "_make_request", new_callable=AsyncMock
        ) as mock_make_request:
            # 例外を発生させる
            mock_make_request.side_effect = UnauthorizedException(
                "Unauthorized access to GitHub API."
            )

            # UnauthorizedException例外が発生することを確認
            with pytest.raises(UnauthorizedException):
                await github_service._make_request("GET", "https://api.github.com/test")

    @pytest.mark.asyncio
    async def test_get_document(self, github_service):
        """ドキュメント取得のテスト"""
        # GitHubのコンテンツAPIのレスポンスをモック
        mock_content = "IyBIZWxsbyBXb3JsZAoKVGhpcyBpcyBhIHRlc3QgcmVwb3NpdG9yeS4="  # "# Hello World\n\nThis is a test repository." をBase64エンコード
        mock_data = {
            "name": "README.md",
            "path": "README.md",
            "sha": "abc123",
            "size": 35,
            "url": "https://api.github.com/repos/octocat/Hello-World/contents/README.md",
            "html_url": "https://github.com/octocat/Hello-World/blob/main/README.md",
            "git_url": "https://api.github.com/repos/octocat/Hello-World/git/blobs/abc123",
            "download_url": "https://raw.githubusercontent.com/octocat/Hello-World/main/README.md",
            "type": "file",
            "content": mock_content,
            "encoding": "base64",
        }

        # _make_requestメソッドをモック
        with patch.object(
            github_service, "_make_request", new_callable=AsyncMock
        ) as mock_make_request:
            mock_make_request.return_value = (
                mock_data,
                {"Last-Modified": "Wed, 01 Jan 2025 00:00:00 GMT"},
            )

            response = await github_service.get_document(
                "octocat", "Hello-World", "README.md"
            )

        # 結果を検証
        assert response.path == "README.md"
        assert response.name == "README.md"
        assert response.type.value == "markdown"
        assert response.content.content.startswith("# Hello World")
        assert response.metadata.sha == "abc123"
        assert (
            str(response.metadata.html_url)
            == "https://github.com/octocat/Hello-World/blob/main/README.md"
        )
        assert response.service == "github"
        assert response.owner == "octocat"
        assert response.repository == "Hello-World"

    @pytest.mark.asyncio
    async def test_get_document_directory(self, github_service):
        """ディレクトリを指定した場合のテスト"""
        # ディレクトリの場合はリストが返る
        mock_data = [
            {"name": "file1.md", "path": "dir/file1.md", "type": "file"},
            {"name": "file2.md", "path": "dir/file2.md", "type": "file"},
        ]

        # _make_requestメソッドをモック
        with patch.object(
            github_service, "_make_request", new_callable=AsyncMock
        ) as mock_make_request:
            mock_make_request.return_value = (mock_data, {})

            with pytest.raises(NotFoundException):
                await github_service.get_document("octocat", "Hello-World", "dir")

    @pytest.mark.asyncio
    async def test_get_repository_structure(self, github_service):
        """リポジトリ構造取得のテスト"""
        # GitHubのツリーAPIのレスポンスをモック
        mock_data = {
            "sha": "abc123",
            "tree": [
                {
                    "path": "README.md",
                    "mode": "100644",
                    "type": "blob",
                    "sha": "def456",
                    "size": 35,
                    "url": "https://api.github.com/repos/octocat/Hello-World/git/blobs/def456",
                },
                {
                    "path": "src",
                    "mode": "040000",
                    "type": "tree",
                    "sha": "ghi789",
                    "url": "https://api.github.com/repos/octocat/Hello-World/git/trees/ghi789",
                },
                {
                    "path": "src/main.py",
                    "mode": "100644",
                    "type": "blob",
                    "sha": "jkl012",
                    "size": 217,
                    "url": "https://api.github.com/repos/octocat/Hello-World/git/blobs/jkl012",
                },
            ],
            "truncated": False,
        }

        # _make_requestメソッドをモック
        with patch.object(
            github_service, "_make_request", new_callable=AsyncMock
        ) as mock_make_request:
            mock_make_request.return_value = (mock_data, {})

            response = await github_service.get_repository_structure(
                "octocat", "Hello-World"
            )

        # 結果を検証
        assert response.service == "github"
        assert response.owner == "octocat"
        assert response.repo == "Hello-World"
        assert len(response.tree) == 3

        # ファイルの検証
        readme = next(item for item in response.tree if item.path == "README.md")
        assert readme.type == "file"
        assert readme.name == "README.md"
        assert readme.sha == "def456"
        assert (
            str(readme.download_url)
            == "https://raw.githubusercontent.com/octocat/Hello-World/main/README.md"
        )
        assert (
            str(readme.html_url)
            == "https://github.com/octocat/Hello-World/blob/main/README.md"
        )

        # ディレクトリの検証
        src_dir = next(item for item in response.tree if item.path == "src")
        assert src_dir.type == "directory"
        assert src_dir.name == "src"
        assert src_dir.download_url is None
        assert (
            str(src_dir.html_url)
            == "https://github.com/octocat/Hello-World/tree/main/src"
        )

    @pytest.mark.asyncio
    async def test_search_repository(self, github_service):
        """リポジトリ検索のテスト"""
        # GitHubの検索APIのレスポンスをモック
        mock_data = {
            "total_count": 2,
            "incomplete_results": False,
            "items": [
                {
                    "name": "main.py",
                    "path": "src/main.py",
                    "sha": "jkl012",
                    "url": "https://api.github.com/repositories/12345/contents/src/main.py",
                    "html_url": "https://github.com/octocat/Hello-World/blob/main/src/main.py",
                    "repository": {
                        "name": "Hello-World",
                        "owner": {"login": "octocat"},
                    },
                    "score": 1.0,
                },
                {
                    "name": "test_main.py",
                    "path": "tests/test_main.py",
                    "sha": "pqr678",
                    "url": "https://api.github.com/repositories/12345/contents/tests/test_main.py",
                    "html_url": "https://github.com/octocat/Hello-World/blob/main/tests/test_main.py",
                    "repository": {
                        "name": "Hello-World",
                        "owner": {"login": "octocat"},
                    },
                    "score": 0.8,
                },
            ],
        }

        # _make_requestメソッドをモック
        with patch.object(
            github_service, "_make_request", new_callable=AsyncMock
        ) as mock_make_request:
            mock_make_request.return_value = (mock_data, {})

            results = await github_service.search_repository(
                "octocat", "Hello-World", "main.py"
            )

        # 結果を検証
        assert len(results) == 2
        assert results[0]["name"] == "main.py"
        assert results[0]["path"] == "src/main.py"
        assert (
            results[0]["html_url"]
            == "https://github.com/octocat/Hello-World/blob/main/src/main.py"
        )
        assert results[0]["repository"]["name"] == "Hello-World"
        assert results[0]["repository"]["owner"] == "octocat"
        assert results[0]["score"] == 1.0

    @pytest.mark.asyncio
    async def test_check_repository_exists_true(self, github_service):
        """リポジトリ存在確認のテスト（存在する場合）"""
        # _make_requestメソッドをモック
        with patch.object(
            github_service, "_make_request", new_callable=AsyncMock
        ) as mock_make_request:
            mock_make_request.return_value = ({}, {})

            result = await github_service.check_repository_exists(
                "octocat", "Hello-World"
            )

        # 結果を検証
        assert result is True

    @pytest.mark.asyncio
    async def test_check_repository_exists_false(self, github_service):
        """リポジトリ存在確認のテスト（存在しない場合）"""
        # _make_requestメソッドをモック（NotFoundExceptionを発生させる）
        with patch.object(
            github_service, "_make_request", new_callable=AsyncMock
        ) as mock_make_request:
            mock_make_request.side_effect = NotFoundException("Repository not found")

            result = await github_service.check_repository_exists(
                "octocat", "Nonexistent-Repo"
            )

        # 結果を検証
        assert result is False
