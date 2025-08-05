"""
リンク変換ユーティリティのテスト。
"""

import pytest

from doc_ai_helper_backend.services.document.utils.links import (
    LinkTransformer,
)


class TestLinkTransformer:
    """リンク変換ユーティリティのテスト"""

    def test_get_document_base_directory_new_method(self):
        """新方式でのベースディレクトリ取得テスト"""
        # 新方式: repository_root + document_root_directory
        base_dir = LinkTransformer._get_document_base_directory(
            path="docs/guide/getting-started.md",
            repository_root="/",
            document_root_directory="docs"
        )
        assert base_dir == "/docs"

        # repository_rootが"/"でない場合
        base_dir = LinkTransformer._get_document_base_directory(
            path="project/docs/guide/getting-started.md",
            repository_root="/project",
            document_root_directory="docs"
        )
        assert base_dir == "/project/docs"

        # document_root_directoryがNoneの場合
        base_dir = LinkTransformer._get_document_base_directory(
            path="README.md",
            repository_root="/",
            document_root_directory=None
        )
        assert base_dir == "/"

    def test_get_document_base_directory_legacy_fallback(self):
        """旧方式フォールバックのテスト"""
        # 新方式のパラメータがNoneの場合は旧方式を使用
        base_dir = LinkTransformer._get_document_base_directory(
            path="docs/guide/getting-started.md",
            repository_root=None,
            document_root_directory=None,
            root_path="docs"
        )
        assert base_dir == "docs"

        # 旧方式もNoneの場合はファイルのディレクトリを使用
        base_dir = LinkTransformer._get_document_base_directory(
            path="docs/guide/getting-started.md",
            repository_root=None,
            document_root_directory=None,
            root_path=None
        )
        assert base_dir == "docs/guide"

    def test_get_document_base_directory_priority(self):
        """新旧方式の優先順位テスト"""
        # 新方式が優先される
        base_dir = LinkTransformer._get_document_base_directory(
            path="docs/guide/getting-started.md",
            repository_root="/",
            document_root_directory="documentation",
            root_path="docs"
        )
        assert base_dir == "/documentation"  # 新方式が優先

    def test_is_external_link(self):
        """外部リンク判定のテスト"""
        # 外部リンク
        assert LinkTransformer.is_external_link("https://github.com")
        assert LinkTransformer.is_external_link("http://example.com")
        assert LinkTransformer.is_external_link("//cdn.example.com/script.js")

        # 内部リンク
        assert not LinkTransformer.is_external_link("./relative.md")
        assert not LinkTransformer.is_external_link("/absolute/path.md")
        assert not LinkTransformer.is_external_link("../parent/file.md")
        assert not LinkTransformer.is_external_link("#anchor")

    def test_resolve_relative_path(self):
        """相対パス解決のテスト"""
        # 相対パスの解決
        assert (
            LinkTransformer.resolve_relative_path("docs/dir", "./file.md")
            == "/docs/dir/file.md"
        )
        assert (
            LinkTransformer.resolve_relative_path("docs/dir", "../parent.md")
            == "/docs/parent.md"
        )
        assert (
            LinkTransformer.resolve_relative_path("docs/dir", "subdir/file.md")
            == "/docs/dir/subdir/file.md"
        )

        # 絶対パスはそのまま
        assert (
            LinkTransformer.resolve_relative_path("docs/dir", "/absolute/path.md")
            == "/absolute/path.md"
        )

    def test_transform_links(self):
        """リンク変換のテスト（画像・静的リソースのみ）"""
        content = """
# リンク変換テスト

- [相対リンク](./file.md)
- [親ディレクトリリンク](../parent.md)
- [サブディレクトリリンク](subdir/file.md)
- [絶対パスリンク](/absolute/path.md)
- [外部リンク](https://github.com)
- [アンカーリンク](#section)

![相対画像](./image.png)
![外部画像](https://example.com/image.jpg)
"""

        path = "docs/dir/document.md"
        base_url = "/api/v1/documents/contents/github/owner/repo"
        service = "github"
        owner = "owner"
        repo = "repo"
        ref = "main"

        transformed = LinkTransformer.transform_links(
            content, path, base_url, service, owner, repo, ref
        )

        # 変換結果をコンソールに出力してデバッグ
        print(f"\nTransformed content:\n{transformed}")

        # 一般リンクは変換されていないことを確認
        assert "[相対リンク](./file.md)" in transformed
        assert "[親ディレクトリリンク](../parent.md)" in transformed
        assert "[サブディレクトリリンク](subdir/file.md)" in transformed
        assert "[絶対パスリンク](/absolute/path.md)" in transformed

        # 画像リンクはCDN URLに変換されていることを確認
        assert "https://raw.githubusercontent.com/owner/repo/main/docs/dir/image.png" in transformed

        # 外部リンクとアンカーリンクは変換されていないことを確認
        assert "https://github.com" in transformed
        assert "(#section)" in transformed
        assert "![外部画像](https://example.com/image.jpg)" in transformed

    def test_transform_html_tags(self):
        """HTMLタグ内のリンク変換のテスト"""
        content = """
# HTMLタグリンク変換テスト

<a href="./relative-link.md">HTMLアンカータグ</a>
<img src="./images/local.png" alt="HTMLイメージタグ">
<link rel="stylesheet" href="./styles/main.css">

<p>段落内の<a href="../parent.md">相対リンク</a>です。</p>

<div class="content">
  <a href="./subdir/nested.md">ネストされたHTMLリンク</a>
  <img src="./assets/icon.svg" alt="アイコン">
</div>

<a href="https://github.com">外部リンク</a>
<img src="https://example.com/image.jpg" alt="外部画像">
<a href="#section">アンカーリンク</a>
"""

        path = "docs/dir/document.md"
        base_url = "/api/v1/documents/contents/github/owner/repo"
        service = "github"
        owner = "owner"
        repo = "repo"
        ref = "main"

        transformed = LinkTransformer.transform_links(
            content, path, base_url, service, owner, repo, ref
        )

        # 変換結果をコンソールに出力してデバッグ
        print(f"\nTransformed HTML content:\n{transformed}")

        # HTMLアンカータグの一般リンクは変換されていないことを確認
        assert '<a href="./relative-link.md">HTMLアンカータグ</a>' in transformed
        assert '<a href="../parent.md">相対リンク</a>' in transformed
        assert '<a href="./subdir/nested.md">ネストされたHTMLリンク</a>' in transformed

        # HTMLイメージタグが正しく変換されているか確認（画像は外部Raw URLに変換）
        assert (
            'src="https://raw.githubusercontent.com/owner/repo/main/docs/dir/images/local.png"'
            in transformed
        )
        assert (
            'src="https://raw.githubusercontent.com/owner/repo/main/docs/dir/assets/icon.svg"'
            in transformed
        )

        # HTMLリンクタグが正しく変換されているか確認
        assert (
            'href="/api/v1/documents/contents/github/owner/repo/docs/dir/styles/main.css?ref=main"'
            in transformed
        )

        # 外部リンクとアンカーリンクは変換されていないことを確認
        assert 'href="https://github.com"' in transformed
        assert 'src="https://example.com/image.jpg"' in transformed
        assert 'href="#section"' in transformed

    def test_transform_html_tags_without_git_info(self):
        """Git情報なしでのHTMLタグ変換のテスト"""
        content = """
<a href="./relative-link.md">HTMLアンカータグ</a>
<img src="./images/local.png" alt="HTMLイメージタグ">
"""

        path = "docs/dir/document.md"
        base_url = "/api/v1/documents/contents/github/owner/repo"

        transformed = LinkTransformer.transform_links(content, path, base_url)

        # Git情報がない場合、一般リンクは変換されない
        assert '<a href="./relative-link.md">HTMLアンカータグ</a>' in transformed
        
        # 画像はフォールバックでAPI経由に変換される
        assert (
            'src="/api/v1/documents/contents/github/owner/repo/docs/dir/images/local.png"'
            in transformed
        )

    def test_transform_complex_html_structures(self):
        """複雑なHTML構造での変換のテスト"""
        content = """
<details>
  <summary>詳細を表示</summary>
  <p>詳細内容に<a href="./details.md">リンク</a>があります。</p>
  <img src="./images/detail.png" alt="詳細画像">
</details>

<table>
  <tr>
    <td><a href="./table-link.md">テーブル内リンク</a></td>
    <td><img src="./icons/check.png" alt="チェック"></td>
  </tr>
</table>
"""

        path = "docs/dir/document.md"
        base_url = "/api/v1/documents/contents/github/owner/repo"
        service = "github"
        owner = "owner"
        repo = "repo"
        ref = "main"

        transformed = LinkTransformer.transform_links(
            content, path, base_url, service, owner, repo, ref
        )

        # 複雑なHTML構造内でも一般リンクは変換されない
        assert '<a href="./details.md">リンク</a>' in transformed
        assert '<a href="./table-link.md">テーブル内リンク</a>' in transformed
        
        # 画像のみ正しく変換されている
        assert (
            'src="https://raw.githubusercontent.com/owner/repo/main/docs/dir/images/detail.png"'
            in transformed
        )
        assert (
            'src="https://raw.githubusercontent.com/owner/repo/main/docs/dir/icons/check.png"'
            in transformed
        )

    def test_transform_links_with_root_path(self):
        """root_pathを使用したリンク変換のテスト"""
        content = """
# Root Path Test

- [相対リンク](./file.md)
- [親ディレクトリリンク](../parent.md)
- [サブディレクトリリンク](subdir/file.md)
- [画像リンク](../images/test.png)

![相対画像](./local.png)
![親ディレクトリ画像](../assets/icon.svg)
"""

        path = "docs/guide/setup.md"
        base_url = "/api/v1/documents/contents/github/owner/repo"
        service = "github"
        owner = "owner"
        repo = "repo"
        ref = "main"

        # root_pathなしの場合（従来の動作）
        transformed_without_root = LinkTransformer.transform_links(
            content, path, base_url, service, owner, repo, ref
        )

        # root_pathありの場合（新しい動作）
        transformed_with_root = LinkTransformer.transform_links(
            content, path, base_url, service, owner, repo, ref, root_path="docs"
        )

        print(f"\nWithout root_path:\n{transformed_without_root}")
        print(f"\nWith root_path:\n{transformed_with_root}")

        # 一般リンクは変換されない
        assert "[相対リンク](./file.md)" in transformed_without_root
        assert "[親ディレクトリリンク](../parent.md)" in transformed_without_root
        assert "[画像リンク](../images/test.png)" in transformed_without_root
        
        assert "[相対リンク](./file.md)" in transformed_with_root
        assert "[親ディレクトリリンク](../parent.md)" in transformed_with_root
        assert "[画像リンク](../images/test.png)" in transformed_with_root

        # 画像の変換も確認
        assert (
            "https://raw.githubusercontent.com/owner/repo/main/docs/guide/local.png"
            in transformed_without_root
        )
        assert (
            "https://raw.githubusercontent.com/owner/repo/main/docs/local.png"
            in transformed_with_root
        )

    def test_transform_links_with_root_path_edge_cases(self):
        """root_pathのエッジケースのテスト"""
        content = """
- [リンク](./file.md)
- [親リンク](../parent.md)
"""

        path = "docs/guide/setup.md"
        base_url = "/api/v1/documents/contents/github/owner/repo"

        # root_pathが空文字列の場合（従来の動作と同じ）
        transformed_empty = LinkTransformer.transform_links(
            content, path, base_url, root_path=""
        )
        assert "[リンク](./file.md)" in transformed_empty

        # root_pathが"/"で終わっている場合
        transformed_slash = LinkTransformer.transform_links(
            content, path, base_url, root_path="docs/"
        )
        assert "[リンク](./file.md)" in transformed_slash

        # root_pathがNoneの場合（一般リンクは変換されない）
        transformed_none = LinkTransformer.transform_links(
            content, path, base_url, root_path=None
        )
        assert "[リンク](./file.md)" in transformed_none
