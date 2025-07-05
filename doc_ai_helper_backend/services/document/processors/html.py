"""
HTMLドキュメント専用プロセッサー。

HTMLファイルの解析、メタデータ抽出、リンク処理を行います。
Quartoやその他の静的サイトジェネレーターで生成されたHTMLに対応しています。
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from doc_ai_helper_backend.models.document import (
    DocumentContent,
    DocumentMetadata,
    HTMLMetadata,
)
from doc_ai_helper_backend.models.link_info import LinkInfo
from doc_ai_helper_backend.services.document.processors.base import (
    DocumentProcessorBase,
)
from doc_ai_helper_backend.services.document.utils.html_analyzer import (
    HTMLAnalyzer,
)

logger = logging.getLogger("doc_ai_helper")


class HTMLProcessor(DocumentProcessorBase):
    """HTML専用ドキュメントプロセッサー"""

    def process_content(self, content: str, path: str) -> DocumentContent:
        """
        HTMLコンテンツを処理する。

        Args:
            content: 生のHTMLコンテンツ
            path: ドキュメントのパス

        Returns:
            処理済みのHTMLコンテンツ
        """
        # HTMLの場合、基本的にはそのままコンテンツを返す
        # 将来的には整形やクリーニングを行う可能性がある
        return DocumentContent(content=content, encoding="utf-8")

    def extract_metadata(self, content: str, path: str) -> DocumentMetadata:
        """
        HTMLドキュメントからメタデータを抽出する。

        Args:
            content: 生のHTMLコンテンツ
            path: ドキュメントのパス

        Returns:
            抽出されたメタデータ
        """
        # HTMLを解析
        soup = HTMLAnalyzer.parse_html_safely(content)

        # 基本的なメタデータを作成
        metadata = DocumentMetadata(
            size=len(content.encode("utf-8")),
            last_modified=datetime.now(timezone.utc),
            content_type="text/html",
            extra={},
        )

        # HTML固有のメタデータを抽出
        html_metadata = self._extract_html_metadata(soup)

        # extraフィールドにHTML固有情報を格納
        metadata.extra["html"] = html_metadata.model_dump()

        return metadata

    def extract_links(self, content: str, base_path: str) -> List[LinkInfo]:
        """
        HTMLドキュメントからリンク情報を抽出する。

        Args:
            content: HTMLコンテンツ
            base_path: ベースパス

        Returns:
            抽出されたリンク情報のリスト
        """
        soup = HTMLAnalyzer.parse_html_safely(content)
        links = []

        # aタグのリンクを抽出
        for link_tag in soup.find_all("a", href=True):
            href = link_tag.get("href")
            text = link_tag.get_text().strip()

            # 位置情報は簡易的に設定（実際のHTML内での位置計算は複雑）
            position = (0, len(text))

            # 外部リンクかどうかを判定
            is_external = self._is_external_link(href)

            links.append(
                LinkInfo(
                    text=text,
                    url=href,
                    is_image=False,
                    position=position,
                    is_external=is_external,
                )
            )

        # imgタグの画像リンクを抽出
        for img_tag in soup.find_all("img", src=True):
            src = img_tag.get("src")
            alt = img_tag.get("alt", "")

            position = (0, len(alt))
            is_external = self._is_external_link(src)

            links.append(
                LinkInfo(
                    text=alt,
                    url=src,
                    is_image=True,
                    position=position,
                    is_external=is_external,
                )
            )

        return links

    def transform_links(
        self, content: str, links: List[LinkInfo], base_url: str
    ) -> str:
        """
        HTMLドキュメント内のリンクを変換する。

        Args:
            content: HTMLコンテンツ
            links: リンク情報のリスト
            base_url: ベースURL

        Returns:
            リンクが変換されたHTMLコンテンツ
        """
        soup = HTMLAnalyzer.parse_html_safely(content)

        # aタグのhref属性を変換
        for link_tag in soup.find_all("a", href=True):
            href = link_tag.get("href")
            if not self._is_external_link(href) and not href.startswith("#"):
                # 相対リンクを絶対URLに変換
                new_href = self._convert_to_absolute_url(href, base_url)
                link_tag["href"] = new_href

        # imgタグのsrc属性を変換
        for img_tag in soup.find_all("img", src=True):
            src = img_tag.get("src")
            if not self._is_external_link(src):
                # 相対リンクを絶対URLに変換
                new_src = self._convert_to_absolute_url(src, base_url)
                img_tag["src"] = new_src

        # その他のアセット（CSS、JS等）も変換
        for link_tag in soup.find_all("link", href=True):
            href = link_tag.get("href")
            if not self._is_external_link(href):
                new_href = self._convert_to_absolute_url(href, base_url)
                link_tag["href"] = new_href

        for script_tag in soup.find_all("script", src=True):
            src = script_tag.get("src")
            if not self._is_external_link(src):
                new_src = self._convert_to_absolute_url(src, base_url)
                script_tag["src"] = new_src

        return str(soup)

    def _extract_html_metadata(self, soup) -> HTMLMetadata:
        """
        BeautifulSoupオブジェクトからHTML固有のメタデータを抽出する。

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            HTML固有のメタデータ
        """
        # 基本的なメタデータ
        title = HTMLAnalyzer.extract_title(soup)
        meta_tags = HTMLAnalyzer.extract_meta_tags(soup)
        headings = HTMLAnalyzer.extract_heading_structure(soup)
        generator = HTMLAnalyzer.detect_generator_tool(soup)
        source_file = HTMLAnalyzer.find_source_file_references(soup)
        lang_charset = HTMLAnalyzer.extract_lang_and_charset(soup)

        # Quartoメタデータ
        quarto_info = HTMLAnalyzer.extract_quarto_metadata(soup)
        build_info = {}
        if quarto_info:
            build_info["quarto"] = quarto_info

        return HTMLMetadata(
            title=title,
            description=meta_tags.get("description"),
            author=meta_tags.get("author"),
            generator=generator,
            source_file=source_file,
            build_info=build_info,
            headings=headings,
            lang=lang_charset["lang"],
            charset=lang_charset["charset"],
        )

    def _is_external_link(self, url: str) -> bool:
        """
        URLが外部リンクかどうかを判定する。

        Args:
            url: 判定するURL

        Returns:
            外部リンクの場合True
        """
        if not url:
            return False

        # 明らかに外部リンクのパターン
        if url.startswith(("http://", "https://", "ftp://", "mailto:")):
            return True

        # 相対リンクやアンカーリンクは内部リンク
        if url.startswith(("/", "./", "../", "#")):
            return False

        # プロトコルが指定されていないが、ドメイン名っぽいもの
        if "." in url and not url.startswith("."):
            # 単純な判定：ドットが含まれていて拡張子っぽくない場合は外部リンクとする
            # より厳密な判定は必要に応じて実装
            parts = url.split(".")
            if len(parts) >= 2 and not parts[-1] in ["html", "htm", "md", "txt", "pdf"]:
                return True

        return False

    def _convert_to_absolute_url(self, relative_url: str, base_url: str) -> str:
        """
        相対URLを絶対URLに変換する。

        Args:
            relative_url: 相対URL
            base_url: ベースURL

        Returns:
            絶対URL
        """
        from urllib.parse import urljoin, urlparse

        # urljoinを使用してより正確なURL結合を行う
        if relative_url.startswith("/"):
            # ルートからの絶対パスの場合、ドメインルートから結合
            parsed = urlparse(base_url)
            return f"{parsed.scheme}://{parsed.netloc}{relative_url}"
        else:
            # 相対パスの場合、base_urlがディレクトリとして扱われるようにスラッシュを確保
            if not base_url.endswith("/"):
                base_url += "/"
            return urljoin(base_url, relative_url)

    # HTML固有の追加メソッド
    def extract_html_title(self, content: str) -> Optional[str]:
        """
        HTMLからタイトルを抽出する。

        Args:
            content: HTMLコンテンツ

        Returns:
            タイトル文字列
        """
        soup = HTMLAnalyzer.parse_html_safely(content)
        return HTMLAnalyzer.extract_title(soup)

    def extract_html_meta_tags(self, content: str) -> Dict[str, str]:
        """
        HTMLからmetaタグ情報を抽出する。

        Args:
            content: HTMLコンテンツ

        Returns:
            metaタグ情報の辞書
        """
        soup = HTMLAnalyzer.parse_html_safely(content)
        return HTMLAnalyzer.extract_meta_tags(soup)

    def extract_html_headings(self, content: str) -> List[Dict[str, Any]]:
        """
        HTMLから見出し構造を抽出する。

        Args:
            content: HTMLコンテンツ

        Returns:
            見出し構造のリスト
        """
        soup = HTMLAnalyzer.parse_html_safely(content)
        return HTMLAnalyzer.extract_heading_structure(soup)

    def extract_source_references(self, content: str) -> Optional[Dict[str, str]]:
        """
        HTMLからソースファイルへの参照を抽出する。

        Args:
            content: HTMLコンテンツ

        Returns:
            ソースファイル情報の辞書
        """
        soup = HTMLAnalyzer.parse_html_safely(content)
        source_file = HTMLAnalyzer.find_source_file_references(soup)
        generator = HTMLAnalyzer.detect_generator_tool(soup)

        if source_file or generator:
            return {"source_file": source_file, "generator": generator}

        return None
