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
