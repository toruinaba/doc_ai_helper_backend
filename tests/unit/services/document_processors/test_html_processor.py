"""
HTMLプロセッサーのユニットテスト。
"""

import pytest
from pathlib import Path

from doc_ai_helper_backend.models.document import DocumentType
from doc_ai_helper_backend.services.document_processors.html_processor import (
    HTMLProcessor,
)


class TestHTMLProcessor:
    """HTMLプロセッサーのテストクラス"""

    @pytest.fixture
    def html_processor(self):
        """HTMLプロセッサーのインスタンスを返す"""
        return HTMLProcessor()

    @pytest.fixture
    def simple_html_content(self):
        """シンプルなHTMLコンテンツを返す"""
        fixtures_dir = Path(__file__).parent.parent.parent.parent / "fixtures" / "html"
        with open(fixtures_dir / "simple.html", "r", encoding="utf-8") as f:
            return f.read()

    @pytest.fixture
    def quarto_html_content(self):
        """Quarto生成HTMLコンテンツを返す"""
        fixtures_dir = Path(__file__).parent.parent.parent.parent / "fixtures" / "html"
        with open(fixtures_dir / "quarto_output.html", "r", encoding="utf-8") as f:
            return f.read()

    @pytest.fixture
    def rich_metadata_html_content(self):
        """リッチメタデータHTMLコンテンツを返す"""
        fixtures_dir = Path(__file__).parent.parent.parent.parent / "fixtures" / "html"
        with open(fixtures_dir / "with_metadata.html", "r", encoding="utf-8") as f:
            return f.read()

    def test_process_content_basic(self, html_processor, simple_html_content):
        """基本的なコンテンツ処理のテスト"""
        # Act
        result = html_processor.process_content(simple_html_content, "test.html")

        # Assert
        assert result.content == simple_html_content
        assert result.encoding == "utf-8"

    def test_extract_metadata_basic(self, html_processor, simple_html_content):
        """基本的なメタデータ抽出のテスト"""
        # Act
        metadata = html_processor.extract_metadata(simple_html_content, "test.html")

        # Assert
        assert metadata.content_type == "text/html"
        assert metadata.size > 0
        assert "html" in metadata.extra

        html_meta = metadata.extra["html"]
        assert html_meta["title"] == "Simple Test Document"
        assert html_meta["description"] == "A simple HTML document for testing"
        assert html_meta["author"] == "Test Author"
        assert html_meta["lang"] == "en"
        assert html_meta["charset"] == "UTF-8"

    def test_extract_metadata_quarto(self, html_processor, quarto_html_content):
        """Quarto生成HTMLのメタデータ抽出テスト"""
        # Act
        metadata = html_processor.extract_metadata(quarto_html_content, "document.html")

        # Assert
        html_meta = metadata.extra["html"]
        assert html_meta["title"] == "Quarto Sample Document"
        assert html_meta["generator"] == "Quarto"
        assert html_meta["source_file"] == "document.qmd"
        assert "quarto" in html_meta["build_info"]

    def test_extract_metadata_rich(self, html_processor, rich_metadata_html_content):
        """リッチメタデータHTMLの抽出テスト"""
        # Act
        metadata = html_processor.extract_metadata(
            rich_metadata_html_content, "rich.html"
        )

        # Assert
        html_meta = metadata.extra["html"]
        assert html_meta["title"] == "Rich Metadata Document"
        assert html_meta["description"] == "Rich metadata HTML document"
        assert html_meta["author"] == "Test Author"
        assert html_meta["lang"] == "ja"
        assert html_meta["charset"] == "UTF-8"

    def test_extract_heading_structure(self, html_processor, simple_html_content):
        """見出し構造抽出のテスト"""
        # Act
        headings = html_processor.extract_html_headings(simple_html_content)

        # Assert
        assert len(headings) == 5

        # h1タグの確認
        h1_headings = [h for h in headings if h["level"] == 1]
        assert len(h1_headings) == 1
        assert h1_headings[0]["text"] == "Main Title"

        # h2タグの確認
        h2_headings = [h for h in headings if h["level"] == 2]
        assert len(h2_headings) == 2
        assert h2_headings[0]["text"] == "Section 1"
        assert h2_headings[1]["text"] == "Section 2"

        # h3タグの確認
        h3_headings = [h for h in headings if h["level"] == 3]
        assert len(h3_headings) == 2
        assert h3_headings[0]["text"] == "Subsection 1.1"
        assert h3_headings[1]["text"] == "Subsection 2.1"

    def test_extract_links_basic(self, html_processor, simple_html_content):
        """基本的なリンク抽出のテスト"""
        # Act
        links = html_processor.extract_links(simple_html_content, "")

        # Assert
        # aタグのリンク
        a_links = [link for link in links if not link.is_image]
        assert len(a_links) == 3

        # 相対リンク
        relative_links = [link for link in a_links if not link.is_external]
        assert len(relative_links) == 2  # ./relative-link.html と #section1

        # 外部リンク
        external_links = [link for link in a_links if link.is_external]
        assert len(external_links) == 1
        assert external_links[0].url == "https://example.com"

        # 画像リンク
        img_links = [link for link in links if link.is_image]
        assert len(img_links) == 1
        assert img_links[0].url == "./images/test.jpg"
        assert img_links[0].text == "Test image"

    def test_transform_links_basic(self, html_processor, simple_html_content):
        """基本的なリンク変換のテスト"""
        # Arrange
        base_url = "https://example.com/docs"
        links = html_processor.extract_links(simple_html_content, "")

        # Act
        transformed_content = html_processor.transform_links(
            simple_html_content, links, base_url
        )

        # Assert
        # 相対リンクが絶対URLに変換されていることを確認
        assert (
            'href="https://example.com/docs/relative-link.html"' in transformed_content
        )
        assert 'src="https://example.com/docs/images/test.jpg"' in transformed_content

        # 外部リンクはそのまま
        assert 'href="https://example.com"' in transformed_content

        # アンカーリンクはそのまま
        assert 'href="#section1"' in transformed_content

    def test_extract_title_specific(self, html_processor, simple_html_content):
        """タイトル抽出の専用メソッドテスト"""
        # Act
        title = html_processor.extract_html_title(simple_html_content)

        # Assert
        assert title == "Simple Test Document"

    def test_extract_meta_tags_specific(
        self, html_processor, rich_metadata_html_content
    ):
        """メタタグ抽出の専用メソッドテスト"""
        # Act
        meta_tags = html_processor.extract_html_meta_tags(rich_metadata_html_content)

        # Assert
        assert meta_tags["description"] == "Rich metadata HTML document"
        assert meta_tags["author"] == "Test Author"
        assert meta_tags["keywords"] == "html, testing, metadata"
        assert meta_tags["robots"] == "index, follow"
        assert meta_tags["og:title"] == "Rich Metadata Document"
        assert meta_tags["twitter:card"] == "summary"

    def test_extract_source_references_quarto(
        self, html_processor, quarto_html_content
    ):
        """ソースファイル参照抽出のテスト"""
        # Act
        source_info = html_processor.extract_source_references(quarto_html_content)

        # Assert
        assert source_info is not None
        assert source_info["source_file"] == "document.qmd"
        assert source_info["generator"] == "Quarto"

    def test_extract_source_references_simple(
        self, html_processor, simple_html_content
    ):
        """ソースファイル参照抽出のテスト（参照なし）"""
        # Act
        source_info = html_processor.extract_source_references(simple_html_content)

        # Assert
        assert source_info is None

    def test_is_external_link_method(self, html_processor):
        """外部リンク判定メソッドのテスト"""
        # 外部リンク
        assert html_processor._is_external_link("https://example.com") == True
        assert html_processor._is_external_link("http://example.com") == True
        assert html_processor._is_external_link("ftp://example.com") == True
        assert html_processor._is_external_link("mailto:test@example.com") == True

        # 内部リンク
        assert html_processor._is_external_link("./relative.html") == False
        assert html_processor._is_external_link("../parent.html") == False
        assert html_processor._is_external_link("/absolute.html") == False
        assert html_processor._is_external_link("#anchor") == False
        assert html_processor._is_external_link("document.html") == False

    def test_convert_to_absolute_url_method(self, html_processor):
        """絶対URL変換メソッドのテスト"""
        base_url = "https://example.com/docs"

        # 相対パス
        assert (
            html_processor._convert_to_absolute_url("./file.html", base_url)
            == "https://example.com/docs/file.html"
        )
        assert (
            html_processor._convert_to_absolute_url("file.html", base_url)
            == "https://example.com/docs/file.html"
        )

        # 絶対パス
        assert (
            html_processor._convert_to_absolute_url("/root.html", base_url)
            == "https://example.com/root.html"
        )

    def test_error_handling_malformed_html(self, html_processor):
        """不正なHTMLに対するエラーハンドリングのテスト"""
        # Arrange
        malformed_html = (
            "<html><head><title>Test</title><body><h1>Header<p>No closing tags"
        )

        # Act & Assert - 例外が発生しないことを確認
        metadata = html_processor.extract_metadata(malformed_html, "malformed.html")
        assert metadata.content_type == "text/html"

        links = html_processor.extract_links(malformed_html, "")
        assert isinstance(links, list)

        content = html_processor.process_content(malformed_html, "malformed.html")
        assert content.content == malformed_html
