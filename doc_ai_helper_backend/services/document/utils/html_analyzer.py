"""
HTML解析用ユーティリティクラス。

HTMLドキュメントからメタデータ、見出し構造、Quartoメタデータなどを
安全に抽出するためのユーティリティ機能を提供します。
"""

import logging
import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger("doc_ai_helper")


class HTMLAnalyzer:
    """HTML解析用ユーティリティクラス"""

    @staticmethod
    def parse_html_safely(content: str) -> BeautifulSoup:
        """
        HTMLコンテンツを安全に解析する。

        Args:
            content: HTMLコンテンツ

        Returns:
            BeautifulSoupオブジェクト
        """
        try:
            # XMLパーサーを優先的に使用（高速で正確）
            soup = BeautifulSoup(content, "lxml")
        except Exception:
            try:
                # XMLパーサーが失敗した場合はhtml.parserを使用
                soup = BeautifulSoup(content, "html.parser")
            except Exception as e:
                logger.warning(f"HTML parsing failed: {e}")
                # フォールバック：基本的なHTMLパーサー
                soup = BeautifulSoup(content, "html.parser")

        return soup

    @staticmethod
    def extract_meta_tags(content_or_soup) -> Dict[str, str]:
        """
        HTMLからmetaタグの情報を抽出する。

        Args:
            content_or_soup: HTMLコンテンツ文字列またはBeautifulSoupオブジェクト

        Returns:
            metaタグの辞書（name/property -> content）
        """
        if isinstance(content_or_soup, str):
            soup = HTMLAnalyzer.parse_html_safely(content_or_soup)
        else:
            soup = content_or_soup

        meta_info = {}

        # metaタグを検索
        for meta in soup.find_all("meta"):
            if meta.get("name"):
                meta_info[meta.get("name")] = meta.get("content", "")
            elif meta.get("property"):
                meta_info[meta.get("property")] = meta.get("content", "")

        return meta_info

    @staticmethod
    def extract_title(content_or_soup) -> Optional[str]:
        """
        HTMLからタイトルを抽出する。

        Args:
            content_or_soup: HTMLコンテンツ文字列またはBeautifulSoupオブジェクト

        Returns:
            ドキュメントのタイトル
        """
        if isinstance(content_or_soup, str):
            soup = HTMLAnalyzer.parse_html_safely(content_or_soup)
        else:
            soup = content_or_soup

        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            return title_tag.string.strip()

        # フォールバック: h1タグを探す
        h1_tag = soup.find("h1")
        if h1_tag and h1_tag.get_text():
            return h1_tag.get_text().strip()

        return None

    @staticmethod
    def extract_heading_structure(soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        HTMLから見出し構造を抽出する。

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            見出し構造のリスト
        """
        headings = []
        heading_tags = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])

        for heading in heading_tags:
            level = int(heading.name[1])  # h1 -> 1, h2 -> 2, etc.
            text = heading.get_text().strip()
            heading_id = heading.get("id")

            headings.append(
                {"level": level, "text": text, "id": heading_id, "tag": heading.name}
            )

        return headings

    @staticmethod
    def extract_quarto_metadata(soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """
        Quartoによって生成されたHTMLからメタデータを抽出する。

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            Quartoメタデータ（見つかった場合）
        """
        quarto_info = {}

        # Quartoのメタデータを検索
        # 通常、data-quarto-* 属性として埋め込まれる
        html_tag = soup.find("html")
        if html_tag:
            for attr_name, attr_value in html_tag.attrs.items():
                if attr_name.startswith("data-quarto-"):
                    quarto_info[attr_name] = attr_value

        # Quartoの特定クラスを検索
        quarto_elements = soup.find_all(class_=re.compile(r"^quarto-"))
        if quarto_elements:
            quarto_info["has_quarto_classes"] = True
            quarto_info["quarto_classes"] = [
                el.get("class") for el in quarto_elements[:5]  # 最初の5個のみ
            ]

        # Quartoの生成情報をmetaタグから検索
        meta_tags = HTMLAnalyzer.extract_meta_tags(soup)
        if "generator" in meta_tags and "quarto" in meta_tags["generator"].lower():
            quarto_info["generator"] = meta_tags["generator"]

        return quarto_info if quarto_info else None

    @staticmethod
    def find_source_file_references(soup: BeautifulSoup) -> Optional[str]:
        """
        HTMLからソースファイルへの参照を検索する。

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            ソースファイルのパス（見つかった場合）
        """
        # Quartoの場合、通常はdata-source属性に記録される
        html_tag = soup.find("html")
        if html_tag and html_tag.get("data-source"):
            return html_tag.get("data-source")

        # commentから検索
        for comment in soup.find_all(
            string=lambda text: isinstance(text, str) and "source:" in text.lower()
        ):
            # "<!-- source: path/to/file.qmd -->" のようなコメントを検索
            source_match = re.search(r"source:\s*([^\s]+)", comment.strip())
            if source_match:
                return source_match.group(1)

        # metaタグから検索
        meta_tags = HTMLAnalyzer.extract_meta_tags(soup)
        if "source-file" in meta_tags:
            return meta_tags["source-file"]

        return None

    @staticmethod
    def detect_generator_tool(soup: BeautifulSoup) -> Optional[str]:
        """
        HTMLの生成ツールを検出する。

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            生成ツール名（検出された場合）
        """
        meta_tags = HTMLAnalyzer.extract_meta_tags(soup)

        # generatorメタタグをチェック
        generator = meta_tags.get("generator", "").lower()
        if generator:
            if "quarto" in generator:
                return "Quarto"
            elif "hugo" in generator:
                return "Hugo"
            elif "jekyll" in generator:
                return "Jekyll"
            elif "gatsby" in generator:
                return "Gatsby"
            elif "next.js" in generator:
                return "Next.js"
            else:
                return generator.title()

        # HTMLのクラスやIDから推測
        if soup.find(class_=re.compile(r"^quarto-")):
            return "Quarto"
        elif soup.find(class_=re.compile(r"^hugo-")):
            return "Hugo"
        elif soup.find(class_=re.compile(r"^jekyll-")):
            return "Jekyll"

        return None

    @staticmethod
    def extract_lang_and_charset(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        """
        HTMLから言語とcharset情報を抽出する。

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            言語とcharset情報の辞書
        """
        result = {"lang": None, "charset": None}

        # html要素のlang属性をチェック
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            result["lang"] = html_tag.get("lang")

        # meta charset をチェック
        charset_meta = soup.find("meta", attrs={"charset": True})
        if charset_meta:
            result["charset"] = charset_meta.get("charset")
        else:
            # http-equiv="Content-Type" をチェック
            content_type_meta = soup.find("meta", attrs={"http-equiv": "Content-Type"})
            if content_type_meta and content_type_meta.get("content"):
                content = content_type_meta.get("content")
                charset_match = re.search(r"charset=([^;]+)", content)
                if charset_match:
                    result["charset"] = charset_match.group(1).strip()

        return result
