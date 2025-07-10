"""
Markdownコンテンツからフロントマターを解析するユーティリティモジュール。
"""

import frontmatter
from typing import Dict, Tuple, Any


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Markdownコンテンツからフロントマターを解析する。

    Args:
        content: 生のMarkdownコンテンツ

    Returns:
        (フロントマター辞書, フロントマー除去済みコンテンツ)のタプル
    """
    try:
        # python-frontmatterを使用してパース
        parsed = frontmatter.loads(content)

        # フロントマターとコンテンツを分離
        frontmatter_dict = parsed.metadata
        content_without_frontmatter = parsed.content

        return frontmatter_dict, content_without_frontmatter
    except Exception as e:
        # パースエラーの場合は空のフロントマターを返す
        return {}, content
