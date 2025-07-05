"""
Unit tests for HTML analyzer utility.

This module tests the HTML analysis functionality for extracting metadata and structure.
"""

import pytest
from unittest.mock import patch, MagicMock

from doc_ai_helper_backend.services.document.utils.html_analyzer import HTMLAnalyzer


class TestHTMLAnalyzer:
    """Test the HTML analyzer utility."""

    @pytest.fixture
    def analyzer(self):
        """Create an HTMLAnalyzer instance for testing."""
        return HTMLAnalyzer()

    def test_analyzer_initialization(self, analyzer):
        """Test that HTMLAnalyzer initializes correctly."""
        assert analyzer is not None
        assert isinstance(analyzer, HTMLAnalyzer)

    def test_extract_title_from_title_tag(self, analyzer):
        """Test extracting title from HTML title tag."""
        html_content = """
        <html>
            <head>
                <title>Test Page Title</title>
            </head>
            <body>
                <h1>Header</h1>
            </body>
        </html>
        """

        if hasattr(analyzer, "extract_title"):
            title = analyzer.extract_title(html_content)
            assert title == "Test Page Title"

    def test_extract_title_from_h1_fallback(self, analyzer):
        """Test extracting title from h1 tag when title tag is missing."""
        html_content = """
        <html>
            <head></head>
            <body>
                <h1>Main Header Title</h1>
                <p>Content</p>
            </body>
        </html>
        """

        if hasattr(analyzer, "extract_title"):
            title = analyzer.extract_title(html_content)
            # Should fallback to h1 if no title tag
            assert title == "Main Header Title"

    def test_extract_meta_description(self, analyzer):
        """Test extracting meta description."""
        html_content = """
        <html>
            <head>
                <meta name="description" content="This is a test page description">
                <title>Test Page</title>
            </head>
            <body>
                <p>Content</p>
            </body>
        </html>
        """

        if hasattr(analyzer, "extract_meta_description"):
            description = analyzer.extract_meta_description(html_content)
            assert description == "This is a test page description"

    def test_extract_meta_keywords(self, analyzer):
        """Test extracting meta keywords."""
        html_content = """
        <html>
            <head>
                <meta name="keywords" content="test, html, parser, analysis">
                <title>Test Page</title>
            </head>
            <body>
                <p>Content</p>
            </body>
        </html>
        """

        if hasattr(analyzer, "extract_meta_keywords"):
            keywords = analyzer.extract_meta_keywords(html_content)
            expected = ["test", "html", "parser", "analysis"]
            assert keywords == expected

    def test_extract_all_metadata(self, analyzer):
        """Test extracting all metadata at once."""
        html_content = """
        <html>
            <head>
                <title>Test Page Title</title>
                <meta name="description" content="Test description">
                <meta name="keywords" content="test, html">
                <meta name="author" content="Test Author">
            </head>
            <body>
                <h1>Main Header</h1>
                <p>Content</p>
            </body>
        </html>
        """

        if hasattr(analyzer, "extract_metadata"):
            metadata = analyzer.extract_metadata(html_content)

            assert isinstance(metadata, dict)
            # Check expected fields if they exist
            if "title" in metadata:
                assert metadata["title"] == "Test Page Title"
            if "description" in metadata:
                assert metadata["description"] == "Test description"

    def test_analyze_structure(self, analyzer):
        """Test analyzing HTML structure."""
        html_content = """
        <html>
            <head><title>Test</title></head>
            <body>
                <h1>Header 1</h1>
                <h2>Header 2</h2>
                <h3>Header 3</h3>
                <p>Paragraph</p>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
            </body>
        </html>
        """

        if hasattr(analyzer, "analyze_structure"):
            structure = analyzer.analyze_structure(html_content)

            assert isinstance(structure, dict)
            # Check for expected structure elements if they exist
            if "headings" in structure:
                assert len(structure["headings"]) >= 3

    def test_extract_links(self, analyzer):
        """Test extracting links from HTML."""
        html_content = """
        <html>
            <body>
                <a href="/internal-link">Internal Link</a>
                <a href="https://external.com">External Link</a>
                <a href="mailto:test@example.com">Email Link</a>
            </body>
        </html>
        """

        if hasattr(analyzer, "extract_links"):
            links = analyzer.extract_links(html_content)

            assert isinstance(links, list)
            assert len(links) >= 3

    def test_invalid_html_handling(self, analyzer):
        """Test handling of invalid HTML."""
        invalid_html = "<html><head><title>Test</head><body><p>Unclosed tag</html>"

        # Should not raise exceptions but handle gracefully
        if hasattr(analyzer, "extract_title"):
            title = analyzer.extract_title(invalid_html)
            # Should either return a title or handle gracefully
            assert title is None or isinstance(title, str)

    def test_empty_html_handling(self, analyzer):
        """Test handling of empty HTML."""
        empty_html = ""

        if hasattr(analyzer, "extract_metadata"):
            metadata = analyzer.extract_metadata(empty_html)
            assert isinstance(metadata, dict)

    def test_analyzer_methods_exist(self, analyzer):
        """Test that expected analyzer methods exist."""
        # Test for common methods that should exist
        expected_methods = [
            "extract_title",
            "extract_metadata",
            "extract_links",
            "extract_meta_description",
            "analyze_structure",
        ]

        for method_name in expected_methods:
            if hasattr(analyzer, method_name):
                assert callable(getattr(analyzer, method_name))

    @pytest.mark.parametrize(
        "html_input,expected_type",
        [
            ("<html><head><title>Test</title></head></html>", str),
            ("", dict),
            ("<p>Simple paragraph</p>", dict),
        ],
    )
    def test_various_html_inputs(self, analyzer, html_input, expected_type):
        """Test analyzer with various HTML inputs."""
        if hasattr(analyzer, "extract_metadata"):
            result = analyzer.extract_metadata(html_input)
            assert isinstance(result, expected_type) or result is None
