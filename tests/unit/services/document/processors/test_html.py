"""
Unit tests for HTMLProcessor.

Tests HTML document processing functionality including content processing,
metadata extraction, link extraction and transformation.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from doc_ai_helper_backend.services.document.processors.html import HTMLProcessor
from doc_ai_helper_backend.models.document import DocumentContent, DocumentMetadata, HTMLMetadata
from doc_ai_helper_backend.models.link_info import LinkInfo


class TestHTMLProcessor:
    """Test the HTML processor functionality."""

    @pytest.fixture
    def processor(self):
        """Create an HTMLProcessor instance for testing."""
        return HTMLProcessor()

    @pytest.fixture
    def simple_html(self):
        """Simple HTML content for testing."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test Document</title>
    <meta name="description" content="Test description">
    <meta name="author" content="Test Author">
</head>
<body>
    <h1>Main Title</h1>
    <p>This is a test paragraph.</p>
    <h2 id="section1">Section 1</h2>
    <p>Section content with <a href="./relative.html">relative link</a>.</p>
    <h3>Subsection</h3>
    <p>Image: <img src="./images/test.jpg" alt="Test image"></p>
</body>
</html>"""

    @pytest.fixture
    def quarto_html(self):
        """Quarto-generated HTML content for testing."""
        return """<!DOCTYPE html>
<html lang="en" data-quarto-version="1.4.0">
<head>
    <meta charset="UTF-8">
    <meta name="generator" content="Quarto 1.4.0">
    <meta name="source-file" content="document.qmd">
    <title>Quarto Document</title>
</head>
<body class="quarto-document">
    <!-- Source: document.qmd -->
    <div class="quarto-header">
        <h1 class="title">Quarto Document</h1>
    </div>
    <div class="quarto-content">
        <h2 id="introduction">Introduction</h2>
        <p>Quarto content.</p>
    </div>
</body>
</html>"""

    @pytest.fixture
    def complex_html(self):
        """Complex HTML with various elements for testing."""
        return """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="description" content="Complex test document">
    <meta name="keywords" content="html, testing">
    <meta property="og:title" content="OG Title">
    <title>Complex Document</title>
    <link rel="stylesheet" href="./styles.css">
</head>
<body>
    <h1 id="main">Main Title</h1>
    <h2>Section</h2>
    <h3>Subsection</h3>
    <h4>Sub-subsection</h4>
    <p>External link: <a href="https://example.com">Example</a></p>
    <p>Internal link: <a href="#main">Back to top</a></p>
    <img src="https://example.com/external.jpg" alt="External image">
    <img src="./local.png" alt="Local image">
    <script src="./app.js"></script>
    <script src="https://cdn.example.com/lib.js"></script>
</body>
</html>"""

    def test_processor_initialization(self, processor):
        """Test that HTMLProcessor initializes correctly."""
        assert processor is not None
        assert isinstance(processor, HTMLProcessor)

    def test_process_content_basic(self, processor, simple_html):
        """Test basic content processing."""
        result = processor.process_content(simple_html, "/test/document.html")
        
        assert isinstance(result, DocumentContent)
        assert result.content == simple_html
        assert result.encoding == "utf-8"

    def test_process_content_empty(self, processor):
        """Test processing empty content."""
        result = processor.process_content("", "/test/empty.html")
        
        assert isinstance(result, DocumentContent)
        assert result.content == ""
        assert result.encoding == "utf-8"

    def test_extract_metadata_basic(self, processor, simple_html):
        """Test basic metadata extraction."""
        metadata = processor.extract_metadata(simple_html, "/test/document.html")
        
        assert isinstance(metadata, DocumentMetadata)
        assert metadata.content_type == "text/html"
        assert metadata.size == len(simple_html.encode("utf-8"))
        assert "html" in metadata.extra
        
        html_meta = metadata.extra["html"]
        assert html_meta["title"] == "Test Document"
        assert html_meta["description"] == "Test description"
        assert html_meta["author"] == "Test Author"
        assert html_meta["lang"] == "en"
        assert html_meta["charset"] == "UTF-8"

    def test_extract_metadata_quarto(self, processor, quarto_html):
        """Test metadata extraction from Quarto document."""
        metadata = processor.extract_metadata(quarto_html, "/test/quarto.html")
        
        html_meta = metadata.extra["html"]
        assert html_meta["title"] == "Quarto Document"
        assert html_meta["generator"] == "Quarto"
        assert html_meta["source_file"] == "document.qmd"
        assert "quarto" in html_meta["build_info"]

    def test_extract_metadata_headings(self, processor, complex_html):
        """Test heading structure extraction."""
        metadata = processor.extract_metadata(complex_html, "/test/complex.html")
        
        html_meta = metadata.extra["html"]
        headings = html_meta["headings"]
        
        assert len(headings) == 4
        assert headings[0] == {"level": 1, "text": "Main Title", "id": "main", "tag": "h1"}
        assert headings[1] == {"level": 2, "text": "Section", "id": None, "tag": "h2"}
        assert headings[2] == {"level": 3, "text": "Subsection", "id": None, "tag": "h3"}
        assert headings[3] == {"level": 4, "text": "Sub-subsection", "id": None, "tag": "h4"}

    def test_extract_links_basic(self, processor, simple_html):
        """Test basic link extraction."""
        links = processor.extract_links(simple_html, "/test")
        
        assert len(links) >= 2  # At least one a tag and one img tag
        
        # Find the relative link
        relative_link = next((link for link in links if link.url == "./relative.html"), None)
        assert relative_link is not None
        assert relative_link.text == "relative link"
        assert not relative_link.is_image
        assert not relative_link.is_external
        
        # Find the image
        image_link = next((link for link in links if link.url == "./images/test.jpg"), None)
        assert image_link is not None
        assert image_link.text == "Test image"
        assert image_link.is_image
        assert not image_link.is_external

    def test_extract_links_external(self, processor, complex_html):
        """Test extraction of external links."""
        links = processor.extract_links(complex_html, "/test")
        
        # Find external link
        external_link = next((link for link in links if link.url == "https://example.com"), None)
        assert external_link is not None
        assert external_link.text == "Example"
        assert not external_link.is_image
        assert external_link.is_external
        
        # Find external image
        external_image = next((link for link in links if link.url == "https://example.com/external.jpg"), None)
        assert external_image is not None
        assert external_image.text == "External image"
        assert external_image.is_image
        assert external_image.is_external

    def test_extract_links_internal_anchors(self, processor, complex_html):
        """Test extraction of internal anchor links."""
        links = processor.extract_links(complex_html, "/test")
        
        # Find internal anchor link
        anchor_link = next((link for link in links if link.url == "#main"), None)
        assert anchor_link is not None
        assert anchor_link.text == "Back to top"
        assert not anchor_link.is_image
        assert not anchor_link.is_external

    def test_transform_links_basic(self, processor, simple_html):
        """Test basic link transformation."""
        base_url = "https://api.example.com/documents"
        
        result = processor.transform_links(
            simple_html, 
            "/test/document.html", 
            base_url,
            service="github",
            owner="testowner",
            repo="testrepo",
            ref="main"
        )
        
        assert "./relative.html" not in result
        assert "https://api.example.com/documents" in result or "https://raw.githubusercontent.com" in result

    def test_transform_links_images_to_raw_url(self, processor, simple_html):
        """Test transformation of images to raw URLs."""
        result = processor.transform_links(
            simple_html,
            "/test/document.html",
            "https://api.example.com/documents",
            service="github",
            owner="testowner", 
            repo="testrepo",
            ref="main"
        )
        
        # Images should be converted to raw GitHub URLs
        assert "https://raw.githubusercontent.com/testowner/testrepo/main" in result

    def test_transform_links_forgejo(self, processor, simple_html):
        """Test link transformation for Forgejo service."""
        with patch("doc_ai_helper_backend.core.config.settings.forgejo_base_url", "https://git.example.com"):
            result = processor.transform_links(
                simple_html,
                "/test/document.html", 
                "https://api.example.com/documents",
                service="forgejo",
                owner="testowner",
                repo="testrepo", 
                ref="main"
            )
            
            assert "https://git.example.com/testowner/testrepo/raw/main" in result

    def test_transform_links_css_js(self, processor, complex_html):
        """Test transformation of CSS and JS links."""
        result = processor.transform_links(
            complex_html,
            "/test/complex.html",
            "https://api.example.com/documents"
        )
        
        # Local CSS and JS should be transformed
        assert "./styles.css" not in result
        assert "./app.js" not in result
        assert "https://api.example.com/documents" in result
        
        # External CDN links should remain unchanged
        assert "https://cdn.example.com/lib.js" in result

    def test_resolve_relative_path_basic(self, processor):
        """Test basic relative path resolution."""
        result = processor._resolve_relative_path("/docs/section", "../images/test.jpg")
        assert result == "/docs/images/test.jpg"

    def test_resolve_relative_path_current_dir(self, processor):
        """Test relative path resolution for current directory."""
        result = processor._resolve_relative_path("/docs/section", "./test.html")
        assert result == "/docs/section/test.html"

    def test_resolve_relative_path_absolute(self, processor):
        """Test handling of absolute paths."""
        result = processor._resolve_relative_path("/docs/section", "/absolute/path.html")
        assert result == "/absolute/path.html"

    def test_is_image_link_various_formats(self, processor):
        """Test image link detection for various formats."""
        assert processor._is_image_link("test.jpg")
        assert processor._is_image_link("image.png")
        assert processor._is_image_link("photo.gif")
        assert processor._is_image_link("icon.svg")
        assert processor._is_image_link("picture.webp")
        assert processor._is_image_link("thumb.avif")
        
        assert not processor._is_image_link("document.html")
        assert not processor._is_image_link("style.css")
        assert not processor._is_image_link("script.js")
        assert not processor._is_image_link("data.json")

    def test_build_raw_url_github(self, processor):
        """Test raw URL building for GitHub."""
        url = processor._build_raw_url("github", "owner", "repo", "main", "/path/file.jpg")
        assert url == "https://raw.githubusercontent.com/owner/repo/main/path/file.jpg"

    def test_build_raw_url_forgejo(self, processor):
        """Test raw URL building for Forgejo."""
        with patch("doc_ai_helper_backend.core.config.settings.forgejo_base_url", "https://git.example.com"):
            url = processor._build_raw_url("forgejo", "owner", "repo", "main", "/path/file.jpg")
            assert url == "https://git.example.com/owner/repo/raw/main/path/file.jpg"

    def test_build_raw_url_unknown_service(self, processor):
        """Test raw URL building for unknown service."""
        url = processor._build_raw_url("unknown", "owner", "repo", "main", "/path/file.jpg")
        assert url is None

    def test_is_external_link_detection(self, processor):
        """Test external link detection."""
        # External links
        assert processor._is_external_link("https://example.com")
        assert processor._is_external_link("http://example.com")
        assert processor._is_external_link("ftp://files.example.com")
        assert processor._is_external_link("mailto:test@example.com")
        
        # Internal/relative links
        assert not processor._is_external_link("./relative.html")
        assert not processor._is_external_link("../parent.html")
        assert not processor._is_external_link("/absolute.html")
        assert not processor._is_external_link("#anchor")
        
        # Edge cases
        assert not processor._is_external_link("")
        assert not processor._is_external_link("document.html")

    def test_convert_to_absolute_url(self, processor):
        """Test relative to absolute URL conversion."""
        base_url = "https://api.example.com/documents"
        
        # Relative paths
        result = processor._convert_to_absolute_url("./test.html", base_url)
        assert result == "https://api.example.com/documents/test.html"
        
        result = processor._convert_to_absolute_url("../other.html", base_url)
        assert result == "https://api.example.com/other.html"
        
        # Absolute paths
        result = processor._convert_to_absolute_url("/absolute.html", base_url)
        assert result == "https://api.example.com/absolute.html"

    def test_extract_html_title(self, processor, simple_html):
        """Test HTML title extraction convenience method."""
        title = processor.extract_html_title(simple_html)
        assert title == "Test Document"

    def test_extract_html_title_fallback_h1(self, processor):
        """Test HTML title extraction with h1 fallback."""
        html_no_title = """<html><body><h1>Header Title</h1></body></html>"""
        title = processor.extract_html_title(html_no_title)
        assert title == "Header Title"

    def test_extract_html_meta_tags(self, processor, complex_html):
        """Test HTML meta tags extraction convenience method."""
        meta_tags = processor.extract_html_meta_tags(complex_html)
        
        assert meta_tags["description"] == "Complex test document"
        assert meta_tags["keywords"] == "html, testing"
        assert meta_tags["og:title"] == "OG Title"

    def test_extract_html_headings(self, processor, complex_html):
        """Test HTML headings extraction convenience method."""
        headings = processor.extract_html_headings(complex_html)
        
        assert len(headings) == 4
        assert headings[0]["level"] == 1
        assert headings[0]["text"] == "Main Title"

    def test_extract_source_references(self, processor, quarto_html):
        """Test source file references extraction."""
        references = processor.extract_source_references(quarto_html)
        
        assert references is not None
        assert references["source_file"] == "document.qmd"
        assert references["generator"] == "Quarto"

    def test_extract_source_references_none(self, processor, simple_html):
        """Test source references extraction when none exist."""
        references = processor.extract_source_references(simple_html)
        # Should return None or empty dict when no references found
        assert references is None or not references

    def test_error_handling_malformed_html(self, processor):
        """Test handling of malformed HTML."""
        malformed_html = "<html><head><title>Test</title><body><h1>Unclosed tag"
        
        # Should not raise an exception
        content = processor.process_content(malformed_html, "/test/malformed.html")
        assert isinstance(content, DocumentContent)
        
        metadata = processor.extract_metadata(malformed_html, "/test/malformed.html")
        assert isinstance(metadata, DocumentMetadata)

    def test_empty_html_handling(self, processor):
        """Test handling of empty or minimal HTML."""
        minimal_html = "<html></html>"
        
        metadata = processor.extract_metadata(minimal_html, "/test/minimal.html")
        assert isinstance(metadata, DocumentMetadata)
        
        links = processor.extract_links(minimal_html, "/test")
        assert isinstance(links, list)
        assert len(links) == 0

    def test_large_html_handling(self, processor):
        """Test handling of large HTML documents."""
        # Create a large HTML document
        large_content = "<html><body>"
        for i in range(1000):
            large_content += f"<p>Paragraph {i} with <a href='link{i}.html'>link {i}</a></p>"
        large_content += "</body></html>"
        
        # Should handle without issues
        links = processor.extract_links(large_content, "/test")
        assert len(links) == 1000  # Should find all 1000 links
        
        metadata = processor.extract_metadata(large_content, "/test/large.html")
        assert isinstance(metadata, DocumentMetadata)

    @pytest.mark.parametrize("file_extension,expected_result", [
        ("test.jpg", True),
        ("image.PNG", True),  # Test case insensitivity
        ("photo.JPEG", True),
        ("icon.svg", True),
        ("document.html", False),
        ("style.css", False),
        ("data.json", False),
        ("", False),
    ])
    def test_is_image_link_parametrized(self, processor, file_extension, expected_result):
        """Parametrized test for image link detection."""
        assert processor._is_image_link(file_extension) == expected_result

    @pytest.mark.parametrize("service,owner,repo,ref,path,expected", [
        ("github", "owner", "repo", "main", "file.jpg", "https://raw.githubusercontent.com/owner/repo/main/file.jpg"),
        ("github", "user", "project", "develop", "/docs/image.png", "https://raw.githubusercontent.com/user/project/develop/docs/image.png"),
        ("unknown", "owner", "repo", "main", "file.jpg", None),
    ])
    def test_build_raw_url_parametrized(self, processor, service, owner, repo, ref, path, expected):
        """Parametrized test for raw URL building."""
        result = processor._build_raw_url(service, owner, repo, ref, path)
        assert result == expected