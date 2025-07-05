"""
HTML ドキュメント API の統合テスト。
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from doc_ai_helper_backend.main import app


class TestHTMLDocumentsAPI:
    """HTML ドキュメント API の統合テストクラス"""

    @pytest.fixture
    def client(self):
        """テストクライアントを返す"""
        return TestClient(app)

    @pytest.fixture
    def sample_html_content(self):
        """サンプルHTMLコンテンツを返す"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Sample HTML document">
    <meta name="author" content="Test Author">
    <title>Sample HTML Document</title>
</head>
<body>
    <h1>Main Title</h1>
    <p>This is a sample HTML document.</p>
    
    <h2>Section 1</h2>
    <p>This section contains a <a href="./relative-link.html">relative link</a>.</p>
    
    <h3>Subsection 1.1</h3>
    <p>This subsection contains an <a href="https://example.com">external link</a>.</p>
</body>
</html>"""

    def test_get_html_document_mock_service(self, client, sample_html_content):
        """
        モックサービスからHTMLドキュメントを取得するテスト
        """
        # Act
        response = client.get(
            "/api/v1/documents/contents/mock/test-owner/test-repo/sample.html"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # 基本的なレスポンス構造を確認
        assert data["path"] == "sample.html"
        assert data["name"] == "sample.html"
        assert data["type"] == "html"
        assert data["service"] == "mock"
        assert data["owner"] == "test-owner"
        assert data["repository"] == "test-repo"

        # コンテンツの確認
        assert "content" in data["content"]
        assert data["content"]["encoding"] == "utf-8"

        # メタデータの確認
        assert data["metadata"]["content_type"] == "text/html"
        assert data["metadata"]["size"] > 0

    def test_get_html_document_with_link_transformation(self, client):
        """
        リンク変換機能を有効にしてHTMLドキュメントを取得するテスト
        """
        # Act
        response = client.get(
            "/api/v1/documents/contents/mock/test-owner/test-repo/sample.html",
            params={"transform_links": True, "base_url": "https://example.com/docs"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # リンク情報が含まれていることを確認
        assert "links" in data
        assert isinstance(data["links"], list)

        # 変換されたコンテンツがあることを確認
        assert "transformed_content" in data

    def test_get_html_document_metadata_extraction(self, client):
        """
        HTMLメタデータ抽出機能のテスト
        """
        # Act
        response = client.get(
            "/api/v1/documents/contents/mock/test-owner/test-repo/with_metadata.html"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # メタデータの確認
        metadata = data["metadata"]
        assert "extra" in metadata
        # 入れ子になった構造をチェック
        extra = metadata["extra"]
        assert "extra" in extra
        assert "html" in extra["extra"]

        # HTML固有メタデータの確認
        html_meta = extra["extra"]["html"]
        assert "title" in html_meta
        assert "description" in html_meta
        assert "author" in html_meta
        assert "charset" in html_meta
        assert "lang" in html_meta

    def test_get_html_document_not_found(self, client):
        """
        存在しないHTMLドキュメントを取得しようとした場合のテスト
        """
        # Act
        response = client.get(
            "/api/v1/documents/contents/mock/test-owner/test-repo/nonexistent.html"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "message" in data

    def test_get_html_document_unsupported_service(self, client):
        """
        サポートされていないGitサービスでHTMLドキュメントを取得しようとした場合のテスト
        """
        # Act
        response = client.get(
            "/api/v1/documents/contents/unsupported/test-owner/test-repo/sample.html"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "message" in data and "Unsupported Git service" in data["message"]

    def test_html_document_response_structure(self, client):
        """
        HTMLドキュメントレスポンスの構造が正しいことを確認するテスト
        """
        # Act
        response = client.get(
            "/api/v1/documents/contents/mock/test-owner/test-repo/sample.html"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # 必須フィールドの確認
        required_fields = [
            "path",
            "name",
            "type",
            "content",
            "metadata",
            "repository",
            "owner",
            "service",
            "ref",
            "links",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # contentオブジェクトの構造確認
        content = data["content"]
        assert "content" in content
        assert "encoding" in content

        # metadataオブジェクトの構造確認
        metadata = data["metadata"]
        metadata_fields = ["size", "last_modified", "content_type"]
        for field in metadata_fields:
            assert field in metadata, f"Missing metadata field: {field}"
