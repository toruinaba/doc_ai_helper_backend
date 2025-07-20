"""
Integration tests for HTMLProcessor using real HTML fixture files.

Tests the HTMLProcessor with actual HTML files to ensure correct processing
of real-world documents including Quarto outputs and complex HTML structures.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from doc_ai_helper_backend.services.document.processors.html import HTMLProcessor
from doc_ai_helper_backend.models.document import DocumentContent, DocumentMetadata


class TestHTMLProcessorIntegration:
    """Integration tests for HTMLProcessor with real files."""

    @pytest.fixture
    def processor(self):
        """Create an HTMLProcessor instance for testing."""
        return HTMLProcessor()

    @pytest.fixture
    def fixtures_path(self):
        """Get path to HTML fixtures."""
        return Path(__file__).parent.parent.parent / "fixtures" / "html"

    @pytest.fixture
    def simple_html_content(self, fixtures_path):
        """Load simple HTML fixture content."""
        simple_path = fixtures_path / "simple.html"
        assert simple_path.exists(), f"Fixture file not found: {simple_path}"
        return simple_path.read_text(encoding="utf-8")

    @pytest.fixture
    def metadata_html_content(self, fixtures_path):
        """Load metadata-rich HTML fixture content."""
        metadata_path = fixtures_path / "with_metadata.html"
        assert metadata_path.exists(), f"Fixture file not found: {metadata_path}"
        return metadata_path.read_text(encoding="utf-8")

    @pytest.fixture
    def quarto_html_content(self, fixtures_path):
        """Load Quarto HTML fixture content."""
        quarto_path = fixtures_path / "quarto_output.html"
        assert quarto_path.exists(), f"Fixture file not found: {quarto_path}"
        return quarto_path.read_text(encoding="utf-8")

    def test_process_simple_html_file(self, processor, simple_html_content):
        """Test processing of simple HTML fixture file."""
        result = processor.process_content(simple_html_content, "/docs/simple.html")
        
        assert isinstance(result, DocumentContent)
        assert result.content == simple_html_content
        assert result.encoding == "utf-8"
        assert len(result.content) > 0

    def test_extract_metadata_simple_html(self, processor, simple_html_content):
        """Test metadata extraction from simple HTML fixture."""
        metadata = processor.extract_metadata(simple_html_content, "/docs/simple.html")
        
        assert isinstance(metadata, DocumentMetadata)
        assert metadata.content_type == "text/html"
        assert "html" in metadata.extra
        
        html_meta = metadata.extra["html"]
        assert html_meta["title"] == "Simple Test Document"
        assert html_meta["description"] == "A simple HTML document for testing"
        assert html_meta["author"] == "Test Author"
        assert html_meta["lang"] == "en"
        assert html_meta["charset"] == "UTF-8"

    def test_extract_metadata_rich_html(self, processor, metadata_html_content):
        """Test metadata extraction from metadata-rich HTML fixture."""
        metadata = processor.extract_metadata(metadata_html_content, "/docs/with_metadata.html")
        
        html_meta = metadata.extra["html"]
        assert html_meta["title"] == "Rich Metadata Document"
        assert html_meta["description"] == "Rich metadata HTML document"
        assert html_meta["author"] == "Test Author"
        assert html_meta["lang"] == "ja"
        assert html_meta["charset"] == "UTF-8"

    def test_extract_metadata_quarto_html(self, processor, quarto_html_content):
        """Test metadata extraction from Quarto HTML fixture."""
        metadata = processor.extract_metadata(quarto_html_content, "/docs/quarto_output.html")
        
        html_meta = metadata.extra["html"]
        assert html_meta["title"] == "Quarto Sample Document"
        assert html_meta["description"] == "Sample Quarto document"
        assert html_meta["author"] == "Quarto User"
        assert html_meta["generator"] == "Quarto"
        assert html_meta["source_file"] == "document.qmd"
        assert "quarto" in html_meta["build_info"]

    def test_extract_headings_simple_html(self, processor, simple_html_content):
        """Test heading extraction from simple HTML fixture."""
        metadata = processor.extract_metadata(simple_html_content, "/docs/simple.html")
        
        headings = metadata.extra["html"]["headings"]
        assert len(headings) >= 3  # Should have h1, h2, h3
        
        # Check main title
        h1_headings = [h for h in headings if h["level"] == 1]
        assert len(h1_headings) == 1
        assert h1_headings[0]["text"] == "Main Title"

    def test_extract_headings_metadata_html(self, processor, metadata_html_content):
        """Test heading extraction from metadata-rich HTML fixture."""
        metadata = processor.extract_metadata(metadata_html_content, "/docs/with_metadata.html")
        
        headings = metadata.extra["html"]["headings"]
        assert len(headings) >= 5  # Should have multiple heading levels
        
        # Check for specific headings
        heading_texts = [h["text"] for h in headings]
        assert "Rich Metadata Document" in heading_texts
        assert "Section 1: Introduction" in heading_texts
        assert "Section 2: Media Content" in heading_texts

    def test_extract_links_simple_html(self, processor, simple_html_content):
        """Test link extraction from simple HTML fixture."""
        links = processor.extract_links(simple_html_content, "/docs")
        
        assert len(links) >= 3  # Should have relative link, external link, and image
        
        # Check for specific links
        link_urls = [link.url for link in links]
        assert "./relative-link.html" in link_urls
        assert "https://example.com" in link_urls
        assert "./images/test.jpg" in link_urls

    def test_extract_links_metadata_html(self, processor, metadata_html_content):
        """Test link extraction from metadata-rich HTML fixture."""
        links = processor.extract_links(metadata_html_content, "/docs")
        
        # Should have various types of links
        link_urls = [link.url for link in links]
        
        # Check for different link types
        assert any("./relative/path.html" in url for url in link_urls)
        assert any("https://external.example.com" in url for url in link_urls)
        assert any("#section" in url for url in link_urls)  # Internal anchors
        
        # Check for images
        image_links = [link for link in links if link.is_image]
        assert len(image_links) >= 2  # Should have local and remote images

    def test_transform_links_simple_html(self, processor, simple_html_content):
        """Test link transformation in simple HTML fixture."""
        base_url = "https://api.example.com/documents"
        
        result = processor.transform_links(
            simple_html_content,
            "/docs/simple.html",
            base_url,
            service="github",
            owner="testuser",
            repo="testproject",
            ref="main"
        )
        
        # Original relative links should be transformed
        assert "./relative-link.html" not in result
        assert "./images/test.jpg" not in result
        
        # Should contain either API URLs or raw GitHub URLs
        assert ("https://api.example.com/documents" in result or 
                "https://raw.githubusercontent.com" in result)

    def test_transform_links_metadata_html(self, processor, metadata_html_content):
        """Test link transformation in metadata-rich HTML fixture."""
        base_url = "https://api.example.com/documents"
        
        result = processor.transform_links(
            metadata_html_content,
            "/docs/with_metadata.html",
            base_url,
            service="github",
            owner="testuser",
            repo="testproject",
            ref="main"
        )
        
        # Local resources should be transformed
        assert "./relative/path.html" not in result
        assert "./images/local-image.jpg" not in result
        assert "./assets/additional.css" not in result
        assert "./scripts/app.js" not in result
        
        # External resources should remain unchanged
        assert "https://external.example.com" in result
        assert "https://cdn.example.com/library.js" in result

    def test_transform_links_forgejo_service(self, processor, simple_html_content):
        """Test link transformation for Forgejo service."""
        with patch("doc_ai_helper_backend.core.config.settings.forgejo_base_url", "https://git.example.com"):
            result = processor.transform_links(
                simple_html_content,
                "/docs/simple.html",
                "https://api.example.com/documents",
                service="forgejo",
                owner="testuser",
                repo="testproject",
                ref="main"
            )
            
            # Should contain Forgejo raw URLs
            assert "https://git.example.com/testuser/testproject/raw/main" in result

    def test_quarto_specific_features(self, processor, quarto_html_content):
        """Test Quarto-specific feature extraction."""
        metadata = processor.extract_metadata(quarto_html_content, "/docs/quarto_output.html")
        
        html_meta = metadata.extra["html"]
        build_info = html_meta["build_info"]
        
        assert "quarto" in build_info
        quarto_info = build_info["quarto"]
        
        # Check for Quarto-specific metadata
        assert "data-quarto-version" in quarto_info or "has_quarto_classes" in quarto_info
        
        # Should detect Quarto as generator
        assert html_meta["generator"] == "Quarto"

    def test_css_js_asset_handling(self, processor, metadata_html_content):
        """Test CSS and JavaScript asset link handling."""
        links = processor.extract_links(metadata_html_content, "/docs")
        
        # Should extract CSS and JS links from the content
        # Note: The extract_links method only handles <a> and <img> tags in the current implementation
        # CSS and JS are handled in transform_links method
        
        result = processor.transform_links(
            metadata_html_content,
            "/docs/with_metadata.html",
            "https://api.example.com/documents"
        )
        
        # Local CSS and JS should be transformed
        assert "./styles/main.css" not in result
        assert "./assets/additional.css" not in result
        assert "./scripts/app.js" not in result
        
        # External resources should remain
        assert "https://cdn.example.com/library.js" in result

    def test_multilingual_support(self, processor, metadata_html_content):
        """Test multilingual HTML document support."""
        metadata = processor.extract_metadata(metadata_html_content, "/docs/with_metadata.html")
        
        html_meta = metadata.extra["html"]
        assert html_meta["lang"] == "ja"  # Japanese language
        
        # Should handle text extraction correctly regardless of language
        headings = html_meta["headings"]
        assert len(headings) > 0
        
        for heading in headings:
            assert "text" in heading
            assert isinstance(heading["text"], str)

    def test_large_document_handling(self, processor, metadata_html_content):
        """Test handling of larger HTML documents."""
        # The metadata HTML fixture is reasonably complex
        metadata = processor.extract_metadata(metadata_html_content, "/docs/with_metadata.html")
        
        assert isinstance(metadata, DocumentMetadata)
        assert metadata.size > 1000  # Should be a substantial document
        
        # Should extract all headings
        headings = metadata.extra["html"]["headings"]
        assert len(headings) >= 5
        
        # Should extract multiple links
        links = processor.extract_links(metadata_html_content, "/docs")
        assert len(links) >= 5

    def test_error_resilience_with_real_files(self, processor, simple_html_content):
        """Test error resilience with real file content."""
        # Introduce some corruption to test resilience
        corrupted_html = simple_html_content.replace("</head>", "")  # Remove closing head tag
        
        # Should still process without throwing exceptions
        content = processor.process_content(corrupted_html, "/docs/corrupted.html")
        assert isinstance(content, DocumentContent)
        
        metadata = processor.extract_metadata(corrupted_html, "/docs/corrupted.html")
        assert isinstance(metadata, DocumentMetadata)
        
        links = processor.extract_links(corrupted_html, "/docs")
        assert isinstance(links, list)

    def test_end_to_end_processing_workflow(self, processor, quarto_html_content):
        """Test complete end-to-end processing workflow."""
        path = "/docs/quarto_output.html"
        base_url = "https://api.example.com/documents"
        
        # Step 1: Process content
        content = processor.process_content(quarto_html_content, path)
        assert isinstance(content, DocumentContent)
        
        # Step 2: Extract metadata
        metadata = processor.extract_metadata(quarto_html_content, path)
        assert isinstance(metadata, DocumentMetadata)
        
        # Step 3: Extract links
        links = processor.extract_links(quarto_html_content, "/docs")
        assert isinstance(links, list)
        
        # Step 4: Transform links
        transformed_content = processor.transform_links(
            quarto_html_content,
            path,
            base_url,
            service="github",
            owner="user",
            repo="project",
            ref="main"
        )
        assert isinstance(transformed_content, str)
        
        # Verify the workflow produced expected results
        html_meta = metadata.extra["html"]
        assert html_meta["title"] == "Quarto Sample Document"
        assert html_meta["generator"] == "Quarto"
        assert len(transformed_content) > 0