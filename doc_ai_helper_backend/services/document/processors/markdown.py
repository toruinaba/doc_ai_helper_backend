"""
Markdownドキュメント処理クラスを提供するモジュール。
"""

import os
import re
from typing import Dict, List, Optional, Any, Tuple

from doc_ai_helper_backend.models.document import DocumentContent, DocumentType
from doc_ai_helper_backend.models.link_info import LinkInfo
from doc_ai_helper_backend.models.frontmatter import ExtendedDocumentMetadata
from doc_ai_helper_backend.services.document.processors.base import (
    DocumentProcessorBase,
)
from doc_ai_helper_backend.services.document.utils.frontmatter import (
    parse_frontmatter,
)
from doc_ai_helper_backend.services.document.utils.links import (
    LinkTransformer,
)


class MarkdownProcessor(DocumentProcessorBase):
    """Markdownドキュメント処理クラス"""

    # Markdownリンクパターン [text](url)
    MD_LINK_PATTERN = r"\[([^\]]+)\]\(([^)]+)\)"

    # イメージパターン ![alt](url)
    IMG_LINK_PATTERN = r"!\[([^\]]*)\]\(([^)]+)\)"

    def process_content(self, content: str, path: str) -> DocumentContent:
        """
        Markdownコンテンツを処理する。

        Args:
            content: 生のMarkdownコンテンツ
            path: ドキュメントのパス

        Returns:
            処理済みのドキュメントコンテンツ
        """
        # フロントマターを取得
        frontmatter, cleaned_content = parse_frontmatter(content)

        return DocumentContent(content=cleaned_content, encoding="utf-8")

    def extract_metadata(self, content: str, path: str) -> ExtendedDocumentMetadata:
        """
        Markdownからメタデータを抽出する。

        Args:
            content: 生のMarkdownコンテンツ
            path: ドキュメントのパス

        Returns:
            抽出されたメタデータ
        """
        # フロントマターを取得
        frontmatter_dict, _ = parse_frontmatter(content)

        # ファイル名と拡張子を取得
        filename = os.path.basename(path)
        extension = os.path.splitext(filename)[1].lstrip(".")

        # タイトルを取得（フロントマターまたは最初の見出し）
        title = frontmatter_dict.get("title", self._extract_title_from_content(content))

        # 日付を文字列として扱う
        date_value = frontmatter_dict.get("date", "")
        if date_value and not isinstance(date_value, str):
            date_value = str(date_value)

        return ExtendedDocumentMetadata(
            filename=filename,
            extension=extension,
            title=title,
            description=frontmatter_dict.get("description", ""),
            author=frontmatter_dict.get("author", ""),
            date=date_value,
            tags=frontmatter_dict.get("tags", []),
            frontmatter=frontmatter_dict,
        )

    def extract_links(self, content: str, path: str) -> List[LinkInfo]:
        """
        Markdownからリンク情報を抽出する。

        Args:
            content: 生のMarkdownコンテンツ
            path: ドキュメントのパス

        Returns:
            抽出されたリンク情報のリスト
        """
        links = []

        # コンテンツを行ごとに処理して、イメージリンクと通常リンクの重複を防ぐ
        for line in content.splitlines():
            # まず画像リンクを抽出
            for match in re.finditer(self.IMG_LINK_PATTERN, line):
                alt_text, url = match.groups()
                links.append(
                    LinkInfo(
                        text=alt_text,
                        url=url,
                        is_image=True,
                        position=match.span(),
                        is_external=LinkTransformer.is_external_link(url),
                    )
                )

            # 次に通常のリンクを抽出（ただし、画像リンクでないもののみ）
            for match in re.finditer(self.MD_LINK_PATTERN, line):
                # 画像リンクとして既に抽出されたものはスキップ
                if not line[: match.start()].strip().endswith("!"):
                    text, url = match.groups()
                    links.append(
                        LinkInfo(
                            text=text,
                            url=url,
                            is_image=False,
                            position=match.span(),
                            is_external=LinkTransformer.is_external_link(url),
                        )
                    )

        return links

    def transform_links(self, content: str, path: str, base_url: str) -> str:
        """
        Markdown内のリンクを変換する。

        Args:
            content: 生のMarkdownコンテンツ
            path: ドキュメントのパス
            base_url: 変換に使用する基本URL

        Returns:
            リンク変換済みのコンテンツ
        """
        return LinkTransformer.transform_links(content, path, base_url)

    def _extract_title_from_content(self, content: str) -> str:
        """
        コンテンツから最初の見出しを抽出してタイトルとして返す。

        Args:
            content: Markdownコンテンツ

        Returns:
            抽出されたタイトル
        """
        # フロントマターを除去
        _, cleaned_content = parse_frontmatter(content)

        # 最初の見出しを検索
        heading_match = re.search(r"^#\s+(.+)$", cleaned_content, re.MULTILINE)
        if heading_match:
            return heading_match.group(1).strip()

        # 見出しが見つからない場合は空文字を返す
        return ""
