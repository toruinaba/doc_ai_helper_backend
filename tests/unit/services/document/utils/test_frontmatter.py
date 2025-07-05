"""
フロントマターパーサーのテスト。
"""

import pytest

from doc_ai_helper_backend.services.document.utils.frontmatter import (
    parse_frontmatter,
)


class TestFrontmatterParser:
    """フロントマターパーサーのテスト"""

    def test_parse_frontmatter_with_valid_frontmatter(self):
        """有効なフロントマターのパースのテスト"""
        content = """---
title: テストタイトル
description: これはテストです
tags:
  - test
  - markdown
---

# テストタイトル

これはテスト文書です。
"""
        frontmatter, cleaned_content = parse_frontmatter(content)

        # フロントマターが正しく抽出されたか確認
        assert frontmatter["title"] == "テストタイトル"
        assert frontmatter["description"] == "これはテストです"
        assert frontmatter["tags"] == ["test", "markdown"]

        # コンテンツからフロントマターが削除されたか確認
        assert cleaned_content.strip().startswith("# テストタイトル")
        assert (
            "---" not in cleaned_content[:10]
        )  # 先頭10文字にフロントマター区切りがないことを確認

    def test_parse_frontmatter_without_frontmatter(self):
        """フロントマターなしのコンテンツのテスト"""
        content = """# タイトルのみ

フロントマターなしのマークダウン文書です。
"""
        frontmatter, cleaned_content = parse_frontmatter(content)

        # 空のフロントマターが返されることを確認
        assert frontmatter == {}

        # コンテンツが変更されていないことを確認（改行の違いを無視）
        assert cleaned_content.strip() == content.strip()

    def test_parse_frontmatter_with_invalid_yaml(self):
        """無効なYAMLフロントマターのテスト"""
        content = """---
title: "タイトル
invalid: yaml: format:
---

# コンテンツ
"""
        frontmatter, cleaned_content = parse_frontmatter(content)

        # パースエラーの場合は空のフロントマターが返されることを確認
        assert frontmatter == {}

        # コンテンツは変更されていないことを確認
        assert cleaned_content == content
