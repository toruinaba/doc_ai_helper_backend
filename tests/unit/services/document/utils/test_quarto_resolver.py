"""
Test suite for QuartoPathResolver utility class.

Tests the Quarto HTML→QMD path resolution functionality including
HTML metadata extraction, _quarto.yml config parsing, and pattern matching.
"""

import pytest
import yaml
from unittest.mock import Mock, patch

from doc_ai_helper_backend.services.document.utils.quarto_resolver import QuartoPathResolver


class TestQuartoPathResolver:
    """Test cases for QuartoPathResolver"""

    def test_extract_source_from_html_comment(self):
        """Test source extraction from HTML comment (most reliable method)"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="generator" content="Quarto 1.3.450">
            <!-- source: docs/guide.qmd -->
        </head>
        <body>
            <h1>Test Document</h1>
        </body>
        </html>
        """
        
        result = QuartoPathResolver.extract_source_from_html(html_content)
        assert result == "docs/guide.qmd"

    def test_extract_source_from_data_attribute(self):
        """Test source extraction from data-source attribute"""
        html_content = """
        <!DOCTYPE html>
        <html data-source="content/posts/post1.qmd">
        <head>
            <meta name="generator" content="Quarto 1.3.450">
        </head>
        <body>
            <h1>Test Document</h1>
        </body>
        </html>
        """
        
        result = QuartoPathResolver.extract_source_from_html(html_content)
        assert result == "content/posts/post1.qmd"

    def test_extract_source_from_meta_tag(self):
        """Test source extraction from meta tag (legacy support)"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="generator" content="Quarto 1.3.450">
            <meta name="source-file" content="pages/about.qmd">
        </head>
        <body>
            <h1>Test Document</h1>
        </body>
        </html>
        """
        
        result = QuartoPathResolver.extract_source_from_html(html_content)
        assert result == "pages/about.qmd"

    def test_extract_source_no_metadata(self):
        """Test source extraction when no metadata is available"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Regular HTML Document</title>
        </head>
        <body>
            <h1>Not a Quarto Document</h1>
        </body>
        </html>
        """
        
        result = QuartoPathResolver.extract_source_from_html(html_content)
        assert result is None

    def test_resolve_from_quarto_config_default_output_dir(self):
        """Test path resolution using default _site output directory"""
        config_content = """
        project:
          type: website
          output-dir: _site
        """
        
        html_path = "_site/docs/guide.html"
        result = QuartoPathResolver.resolve_from_quarto_config(html_path, config_content)
        assert result == "docs/guide.qmd"

    def test_resolve_from_quarto_config_custom_output_dir(self):
        """Test path resolution using custom output directory"""
        config_content = """
        project:
          type: website
          output-dir: public
        """
        
        html_path = "public/blog/post1.html"
        result = QuartoPathResolver.resolve_from_quarto_config(html_path, config_content)
        assert result == "blog/post1.qmd"

    def test_resolve_from_quarto_config_github_pages(self):
        """Test path resolution for GitHub Pages setup"""
        config_content = """
        project:
          type: website
          output-dir: docs
        """
        
        html_path = "docs/index.html"
        result = QuartoPathResolver.resolve_from_quarto_config(html_path, config_content)
        assert result == "index.qmd"

    def test_resolve_from_quarto_config_no_match(self):
        """Test path resolution when HTML path doesn't match output directory"""
        config_content = """
        project:
          type: website
          output-dir: _site
        """
        
        html_path = "other/path/file.html"
        result = QuartoPathResolver.resolve_from_quarto_config(html_path, config_content)
        assert result is None

    def test_resolve_from_quarto_config_invalid_yaml(self):
        """Test handling of invalid YAML content"""
        config_content = """
        invalid: yaml: content: [
        """
        
        html_path = "_site/docs/guide.html"
        result = QuartoPathResolver.resolve_from_quarto_config(html_path, config_content)
        assert result is None

    def test_apply_standard_patterns_site_dir(self):
        """Test standard pattern matching for _site directory"""
        html_path = "_site/tutorials/intro.html"
        result = QuartoPathResolver.apply_standard_patterns(html_path)
        assert result == "tutorials/intro.qmd"

    def test_apply_standard_patterns_docs_dir(self):
        """Test standard pattern matching for docs directory (GitHub Pages)"""
        html_path = "docs/api/reference.html"
        result = QuartoPathResolver.apply_standard_patterns(html_path)
        assert result == "api/reference.qmd"

    def test_apply_standard_patterns_public_dir(self):
        """Test standard pattern matching for public directory"""
        html_path = "public/blog/post.html"
        result = QuartoPathResolver.apply_standard_patterns(html_path)
        assert result == "src/blog/post.qmd"

    def test_apply_standard_patterns_same_directory(self):
        """Test pattern matching for same directory (simple sites)"""
        html_path = "index.html"
        result = QuartoPathResolver.apply_standard_patterns(html_path)
        assert result == "index.qmd"

    def test_apply_standard_patterns_no_match(self):
        """Test pattern matching when file is not HTML"""
        html_path = "document.pdf"
        result = QuartoPathResolver.apply_standard_patterns(html_path)
        assert result is None

    def test_is_quarto_html_generator_meta(self):
        """Test Quarto HTML detection via generator meta tag"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="generator" content="Quarto 1.3.450">
        </head>
        <body>
            <h1>Test Document</h1>
        </body>
        </html>
        """
        
        result = QuartoPathResolver.is_quarto_html(html_content)
        assert result is True

    def test_is_quarto_html_data_attributes(self):
        """Test Quarto HTML detection via data attributes"""
        html_content = """
        <!DOCTYPE html>
        <html data-quarto-version="1.3.450">
        <head>
            <title>Test Document</title>
        </head>
        <body>
            <div class="quarto-container">
                <h1>Test Document</h1>
            </div>
        </body>
        </html>
        """
        
        result = QuartoPathResolver.is_quarto_html(html_content)
        assert result is True

    def test_is_quarto_html_false(self):
        """Test Quarto HTML detection for non-Quarto HTML"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Regular HTML Document</title>
        </head>
        <body>
            <h1>Not a Quarto Document</h1>
        </body>
        </html>
        """
        
        result = QuartoPathResolver.is_quarto_html(html_content)
        assert result is False

    def test_extract_quarto_version_from_generator(self):
        """Test Quarto version extraction from generator meta tag"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="generator" content="Quarto 1.3.450">
        </head>
        <body>
            <h1>Test Document</h1>
        </body>
        </html>
        """
        
        result = QuartoPathResolver.extract_quarto_version(html_content)
        assert result == "1.3.450"

    def test_extract_quarto_version_from_data_attribute(self):
        """Test Quarto version extraction from data attribute"""
        html_content = """
        <!DOCTYPE html>
        <html data-quarto-version="1.4.0">
        <head>
            <meta name="generator" content="Quarto">
        </head>
        <body>
            <h1>Test Document</h1>
        </body>
        </html>
        """
        
        result = QuartoPathResolver.extract_quarto_version(html_content)
        assert result == "1.4.0"

    def test_extract_quarto_version_no_version(self):
        """Test Quarto version extraction when no version info available"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="generator" content="Hugo">
        </head>
        <body>
            <h1>Not a Quarto Document</h1>
        </body>
        </html>
        """
        
        result = QuartoPathResolver.extract_quarto_version(html_content)
        assert result is None

    def test_extract_source_priority_order(self):
        """Test that source extraction follows correct priority order"""
        html_content = """
        <!DOCTYPE html>
        <html data-source="data-attr-source.qmd">
        <head>
            <meta name="generator" content="Quarto 1.3.450">
            <meta name="source-file" content="meta-tag-source.qmd">
            <!-- source: comment-source.qmd -->
        </head>
        <body>
            <h1>Test Document</h1>
        </body>
        </html>
        """
        
        # HTML comment should have highest priority
        result = QuartoPathResolver.extract_source_from_html(html_content)
        assert result == "comment-source.qmd"

    @patch('doc_ai_helper_backend.services.document.utils.quarto_resolver.logger')
    def test_error_handling_malformed_html(self, mock_logger):
        """Test error handling for malformed HTML content"""
        malformed_html = "<html><head><title>Incomplete"
        
        result = QuartoPathResolver.extract_source_from_html(malformed_html)
        assert result is None

    def test_nested_directory_patterns(self):
        """Test pattern matching for deeply nested directories"""
        html_path = "_site/deep/nested/structure/document.html"
        result = QuartoPathResolver.apply_standard_patterns(html_path)
        assert result == "deep/nested/structure/document.qmd"

    def test_index_file_patterns(self):
        """Test pattern matching for index files"""
        html_path = "_site/section/index.html"
        result = QuartoPathResolver.apply_standard_patterns(html_path)
        assert result == "section/index.qmd"