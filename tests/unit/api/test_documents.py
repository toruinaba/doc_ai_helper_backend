"""
Test document-related endpoints.
"""

import pytest

from doc_ai_helper_backend.core.config import settings
from doc_ai_helper_backend.api.endpoints import documents


def test_get_document(client):
    """Test get document endpoint."""
    # Test with mock service
    response = client.get(
        f"{settings.api_prefix}/documents/contents/mock/octocat/Hello-World/README.md"
    )

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["path"] == "README.md"
    assert data["name"] == "README.md"
    assert data["type"] == "markdown"
    assert data["service"] == "mock"
    assert data["owner"] == "octocat"
    assert data["repository"] == "Hello-World"
    assert "content" in data
    assert "metadata" in data
    assert data["content"]["content"].startswith("# Hello World")


def test_get_document_not_found(client):
    """Test get document endpoint with not found error."""
    # Test with non-existent document
    response = client.get(
        f"{settings.api_prefix}/documents/contents/mock/octocat/Hello-World/nonexistent.md"
    )

    # Verify
    assert response.status_code == 404
    assert "message" in response.json()
    assert "not found" in response.json()["message"].lower()


def test_get_repository_structure(client):
    """Test get repository structure endpoint."""
    # Test with mock service
    response = client.get(
        f"{settings.api_prefix}/documents/structure/mock/octocat/Hello-World"
    )

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "mock"
    assert data["owner"] == "octocat"
    assert data["repo"] == "Hello-World"
    assert "tree" in data
    assert len(data["tree"]) >= 3  # At least README.md, docs folder, and docs/index.md

    # Find README.md in tree
    readme = next((item for item in data["tree"] if item["path"] == "README.md"), None)
    assert readme is not None
    assert readme["name"] == "README.md"
    assert readme["type"] == "file"


def test_get_repository_structure_not_found(client):
    """Test get repository structure endpoint with not found error."""
    # Test with non-existent repository
    response = client.get(
        f"{settings.api_prefix}/documents/structure/mock/nonexistent/repo"
    )

    # Verify
    assert response.status_code == 404
    assert "message" in response.json()
    assert "not found" in response.json()["message"].lower()


def test_unsupported_git_service(client):
    """Test unsupported Git service."""
    # Test accessing endpoint with unsupported Git service
    response = client.get(
        f"{settings.api_prefix}/documents/contents/gitlab/octocat/Hello-World/README.md"
    )

    # Verify not found or error response
    assert response.status_code == 404
    assert (
        "unsupported" in response.json()["message"].lower()
        or "not found" in response.json()["message"].lower()
    )


def test_get_document_no_link_transformation(client):
    """リンク変換を無効にしたドキュメント取得エンドポイントのテスト。"""
    # モックサービスでtransform_links=Falseをテスト
    response = client.get(
        f"{settings.api_prefix}/documents/contents/mock/octocat/Hello-World/README.md?transform_links=false"
    )

    # 検証
    assert response.status_code == 200
    data = response.json()
    # 変換が無効の場合、transformed_contentはNoneであること
    assert data["transformed_content"] is None
    # 他の基本的なフィールドの検証
    assert data["path"] == "README.md"
    assert data["service"] == "mock"


def test_get_document_with_custom_base_url(client):
    """カスタムベースURLを指定したドキュメント取得エンドポイントのテスト。"""
    # モックサービスでカスタムbase_urlをテスト
    custom_base_url = "https://custom-example.com/docs"
    response = client.get(
        f"{settings.api_prefix}/documents/contents/mock/octocat/Hello-World/README.md?base_url={custom_base_url}"
    )

    # 検証
    assert response.status_code == 200
    data = response.json()
    # transformed_contentが存在する場合、カスタムベースURLが含まれているか、リンクがない場合は問題なし
    if data["transformed_content"] is not None:
        assert custom_base_url in data["transformed_content"] or not data["links"]
    # 他の基本的なフィールドの検証
    assert data["path"] == "README.md"


def test_get_document_with_links(client):
    """リンクを含むドキュメントのテスト。"""
    # リンクを含むドキュメントでテスト
    # ドキュメントのパスはモックデータに基づいて選択
    response = client.get(
        f"{settings.api_prefix}/documents/contents/mock/octocat/Hello-World/docs/index.md"
    )

    # 検証
    assert response.status_code == 200
    data = response.json()
    # リンクフィールドが存在することを確認
    assert "links" in data
    assert isinstance(data["links"], list)
    # リンクがある場合、期待される構造を持っているか確認
    if data["links"]:
        link = data["links"][0]
        assert "text" in link
        assert "url" in link
        assert "is_image" in link
        assert "position" in link
        assert "is_external" in link

    # リンクがある場合、transformed_contentが存在することを確認
    if data["links"]:
        assert data["transformed_content"] is not None


def test_get_document_with_specific_ref(client):
    """特定のrefを指定したドキュメント取得エンドポイントのテスト。"""
    # 特定のブランチまたはタグでテスト
    custom_ref = "develop"
    response = client.get(
        f"{settings.api_prefix}/documents/contents/mock/octocat/Hello-World/README.md?ref={custom_ref}"
    )

    # 検証
    assert response.status_code == 200
    data = response.json()
    assert data["ref"] == custom_ref


def test_get_document_with_multiple_parameters(client):
    """複数のパラメータを組み合わせたドキュメント取得エンドポイントのテスト。"""
    # 複数のパラメータを組み合わせてテスト
    custom_ref = "develop"
    custom_base_url = "https://custom-example.com/docs"
    response = client.get(
        f"{settings.api_prefix}/documents/contents/mock/octocat/Hello-World/README.md"
        f"?ref={custom_ref}&transform_links=true&base_url={custom_base_url}"
    )

    # 検証
    assert response.status_code == 200
    data = response.json()
    assert data["ref"] == custom_ref
    # 変換されたコンテンツがある場合、カスタムベースURLが使用されているか確認
    if data["transformed_content"] is not None:
        assert custom_base_url in data["transformed_content"] or not data["links"]


def test_get_document_no_link_transformation(client):
    """リンク変換を無効にしたドキュメント取得エンドポイントのテスト。"""
    # モックサービスでtransform_links=Falseをテスト
    response = client.get(
        f"{settings.api_prefix}/documents/contents/mock/octocat/Hello-World/README.md?transform_links=false"
    )

    # 検証
    assert response.status_code == 200
    data = response.json()
    # 変換が無効の場合、transformed_contentはNoneであること
    assert data["transformed_content"] is None
    # 他の基本的なフィールドの検証
    assert data["path"] == "README.md"
    assert data["service"] == "mock"


def test_get_document_with_custom_base_url(client):
    """カスタムベースURLを指定したドキュメント取得エンドポイントのテスト。"""
    # モックサービスでカスタムbase_urlをテスト
    custom_base_url = "https://custom-example.com/docs"
    response = client.get(
        f"{settings.api_prefix}/documents/contents/mock/octocat/Hello-World/README.md?base_url={custom_base_url}"
    )

    # 検証
    assert response.status_code == 200
    data = response.json()
    # transformed_contentが存在する場合、カスタムベースURLが含まれているか、リンクがない場合は問題なし
    if data["transformed_content"] is not None:
        assert custom_base_url in data["transformed_content"] or not data["links"]
    # 他の基本的なフィールドの検証
    assert data["path"] == "README.md"


def test_get_document_with_links(client):
    """リンクを含むドキュメントのテスト。"""
    # リンクを含むドキュメントでテスト
    # ドキュメントのパスはモックデータに基づいて選択
    response = client.get(
        f"{settings.api_prefix}/documents/contents/mock/octocat/Hello-World/docs/index.md"
    )

    # 検証
    assert response.status_code == 200
    data = response.json()
    # リンクフィールドが存在することを確認
    assert "links" in data
    assert isinstance(data["links"], list)
    # リンクがある場合、期待される構造を持っているか確認
    if data["links"]:
        link = data["links"][0]
        assert "text" in link
        assert "url" in link
        assert "is_image" in link
        assert "position" in link
        assert "is_external" in link

    # リンクがある場合、transformed_contentが存在することを確認
    if data["links"]:
        assert data["transformed_content"] is not None


def test_get_document_with_specific_ref(client):
    """特定のrefを指定したドキュメント取得エンドポイントのテスト。"""
    # 特定のブランチまたはタグでテスト
    custom_ref = "develop"
    response = client.get(
        f"{settings.api_prefix}/documents/contents/mock/octocat/Hello-World/README.md?ref={custom_ref}"
    )

    # 検証
    assert response.status_code == 200
    data = response.json()
    assert data["ref"] == custom_ref


def test_get_document_with_multiple_parameters(client):
    """複数のパラメータを組み合わせたドキュメント取得エンドポイントのテスト。"""
    # 複数のパラメータを組み合わせてテスト
    custom_ref = "develop"
    custom_base_url = "https://custom-example.com/docs"
    response = client.get(
        f"{settings.api_prefix}/documents/contents/mock/octocat/Hello-World/README.md"
        f"?ref={custom_ref}&transform_links=true&base_url={custom_base_url}"
    )

    # 検証
    assert response.status_code == 200
    data = response.json()
    assert data["ref"] == custom_ref
    # 変換されたコンテンツがある場合、カスタムベースURLが使用されているか確認
    if data["transformed_content"] is not None:
        assert custom_base_url in data["transformed_content"] or not data["links"]


def test_get_document_with_frontmatter(client):
    """フロントマターを含むドキュメントのテスト。"""
    # フロントマターを含むドキュメントでテスト
    # ドキュメントのパスはモックデータに基づいて選択
    response = client.get(
        f"{settings.api_prefix}/documents/contents/mock/example/docs-project/index.md"
    )

    # 検証
    assert response.status_code == 200
    data = response.json()

    # メタデータ内にフロントマターが存在することを確認
    assert "metadata" in data
    assert "frontmatter" in data["metadata"]["extra"]

    # 特定のフロントマターフィールドの存在と値を検証
    frontmatter = data["metadata"]["extra"]["frontmatter"]
    if "title" in frontmatter:
        assert data["metadata"]["extra"]["title"] == frontmatter["title"]
    assert isinstance(frontmatter, dict)


def test_get_document_without_frontmatter(client):
    """フロントマターを含まないドキュメントのテスト。"""
    # フロントマターを含まないドキュメントでテスト
    response = client.get(
        f"{settings.api_prefix}/documents/contents/mock/octocat/Hello-World/README.md"
    )

    # 検証
    assert response.status_code == 200
    data = response.json()

    # フロントマターがない場合、空の辞書または基本的な値のみを持つことを確認
    assert "metadata" in data
    assert data["metadata"]["extra"]["frontmatter"] == {}
