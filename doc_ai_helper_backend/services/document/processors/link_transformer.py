"""
Markdownドキュメント内のリンクを変換するユーティリティモジュール。
"""

import os
import re
from typing import Match, Optional
from urllib.parse import urljoin, urlparse


class LinkTransformer:
    """Markdownドキュメント内のリンクを変換するユーティリティクラス。"""

    # Markdownリンクパターン [text](url)
    MD_LINK_PATTERN = r"\[([^\]]+)\]\(([^)]+)\)"

    # イメージパターン ![alt](url)
    IMG_LINK_PATTERN = r"!\[([^\]]*)\]\(([^)]+)\)"

    @staticmethod
    def is_external_link(url: str) -> bool:
        """
        URLが外部リンクかどうかを判定する。

        Args:
            url: チェックするURL

        Returns:
            外部リンクの場合True
        """
        return bool(urlparse(url).netloc)

    @staticmethod
    def resolve_relative_path(base_dir: str, rel_path: str) -> str:
        """
        相対パスを解決する。

        Args:
            base_dir: 基準ディレクトリ
            rel_path: 相対パス

        Returns:
            解決された絶対パス
        """
        # 絶対パスの場合はそのまま返す
        if rel_path.startswith("/"):
            return rel_path

        # 相対パスを結合
        abs_path = os.path.normpath(os.path.join(base_dir, rel_path))

        # パス区切り文字をスラッシュに統一
        abs_path = abs_path.replace("\\", "/")

        # 先頭のスラッシュを付与
        if not abs_path.startswith("/"):
            abs_path = "/" + abs_path

        return abs_path

    @classmethod
    def transform_links(cls, content: str, path: str, base_url: str) -> str:
        """
        Markdown内のリンクを変換する。

        Args:
            content: 生のMarkdownコンテンツ
            path: ドキュメントのパス
            base_url: 変換に使用する基本URL

        Returns:
            リンク変換済みのコンテンツ
        """
        transformed_content = content

        # ドキュメントのベースディレクトリを取得
        base_dir = os.path.dirname(path)

        # 通常のリンクを変換
        transformed_content = re.sub(
            cls.MD_LINK_PATTERN,
            lambda m: cls._transform_link_match(m, base_dir, base_url),
            transformed_content,
        )

        # 画像リンクを変換
        transformed_content = re.sub(
            cls.IMG_LINK_PATTERN,
            lambda m: cls._transform_image_match(m, base_dir, base_url),
            transformed_content,
        )

        return transformed_content

    @classmethod
    def _transform_link_match(cls, match: Match, base_dir: str, base_url: str) -> str:
        """
        リンクマッチを変換する。

        Args:
            match: 正規表現マッチオブジェクト
            base_dir: 基準ディレクトリ
            base_url: 変換に使用する基本URL

        Returns:
            変換されたリンク文字列
        """
        text, url = match.groups()

        # 外部リンクはそのまま
        if cls.is_external_link(url):
            return f"[{text}]({url})"

        # アンカーリンクはそのまま
        if url.startswith("#"):
            return f"[{text}]({url})"

        # 相対パスを絶対パスに変換
        abs_path = cls.resolve_relative_path(base_dir, url)

        # base_urlの末尾にスラッシュがなければ追加
        if not base_url.endswith("/"):
            base_url = base_url + "/"

        transformed_url = base_url + abs_path.lstrip("/")

        return f"[{text}]({transformed_url})"

    @classmethod
    def _transform_image_match(cls, match: Match, base_dir: str, base_url: str) -> str:
        """
        画像マッチを変換する。

        Args:
            match: 正規表現マッチオブジェクト
            base_dir: 基準ディレクトリ
            base_url: 変換に使用する基本URL

        Returns:
            変換された画像リンク文字列
        """
        alt_text, url = match.groups()

        # 外部リンクはそのまま
        if cls.is_external_link(url):
            return f"![{alt_text}]({url})"

        # 相対パスを絶対パスに変換
        abs_path = cls.resolve_relative_path(base_dir, url)

        # base_urlの末尾にスラッシュがなければ追加
        if not base_url.endswith("/"):
            base_url = base_url + "/"

        transformed_url = base_url + abs_path.lstrip("/")

        return f"![{alt_text}]({transformed_url})"
