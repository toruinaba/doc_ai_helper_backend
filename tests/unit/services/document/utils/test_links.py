"""
リンク変換ユーティリティのテスト。
"""

import pytest

from doc_ai_helper_backend.services.document.utils.links import (
    LinkTransformer,
)


class TestLinkTransformer:
    """リンク変換ユーティリティのテスト"""

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
        """リンク変換のテスト"""
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

        transformed = LinkTransformer.transform_links(content, path, base_url)

        # 変換結果をコンソールに出力してデバッグ
        print(f"\nTransformed content:\n{transformed}")

        # リンクが正しく変換されているか確認
        assert (
            "/api/v1/documents/contents/github/owner/repo/docs/dir/file.md"
            in transformed
        )
        assert (
            "/api/v1/documents/contents/github/owner/repo/docs/parent.md" in transformed
        )
        assert (
            "/api/v1/documents/contents/github/owner/repo/docs/dir/subdir/file.md"
            in transformed
        )
        assert (
            "/api/v1/documents/contents/github/owner/repo/absolute/path.md"
            in transformed
        )

        # 外部リンクとアンカーリンクは変換されていないことを確認
        assert "https://github.com" in transformed
        assert "(#section)" in transformed

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

        # HTMLアンカータグが正しく変換されているか確認
        assert (
            'href="/api/v1/documents/contents/github/owner/repo/docs/dir/relative-link.md?ref=main"'
            in transformed
        )
        assert (
            'href="/api/v1/documents/contents/github/owner/repo/docs/parent.md?ref=main"'
            in transformed
        )
        assert (
            'href="/api/v1/documents/contents/github/owner/repo/docs/dir/subdir/nested.md?ref=main"'
            in transformed
        )

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

        # Git情報がない場合はAPI経由で変換
        assert (
            'href="/api/v1/documents/contents/github/owner/repo/docs/dir/relative-link.md"'
            in transformed
        )
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

        # 複雑なHTML構造内でも正しく変換されているか確認
        assert (
            'href="/api/v1/documents/contents/github/owner/repo/docs/dir/details.md?ref=main"'
            in transformed
        )
        assert (
            'src="https://raw.githubusercontent.com/owner/repo/main/docs/dir/images/detail.png"'
            in transformed
        )
        assert (
            'href="/api/v1/documents/contents/github/owner/repo/docs/dir/table-link.md?ref=main"'
            in transformed
        )
        assert (
            'src="https://raw.githubusercontent.com/owner/repo/main/docs/dir/icons/check.png"'
            in transformed
        )
