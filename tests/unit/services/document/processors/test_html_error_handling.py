"""
Error handling tests for HTMLProcessor.

Tests HTMLProcessor's robustness when dealing with malformed HTML,
edge cases, and error conditions.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
import logging

from doc_ai_helper_backend.services.document.processors.html import HTMLProcessor
from doc_ai_helper_backend.models.document import DocumentContent, DocumentMetadata
from doc_ai_helper_backend.models.link_info import LinkInfo


class TestHTMLProcessorErrorHandling:
    """Test error handling and edge cases in HTMLProcessor."""

    @pytest.fixture
    def processor(self):
        """Create an HTMLProcessor instance for testing."""
        return HTMLProcessor()

    @pytest.fixture
    def malformed_html_samples(self):
        """Various malformed HTML samples for testing."""
        return {
            "unclosed_tags": "<html><head><title>Test</title><body><h1>Unclosed",
            "invalid_nesting": "<html><head><body><title>Wrong nesting</title></head></body></html>",
            "broken_attributes": '<html><head><title>Test</title></head><body><a href="broken>Link</a></body></html>',
            "missing_quotes": '<html><head><title>Test</title></head><body><img src=image.jpg alt=test></body></html>',
            "invalid_entities": "<html><body><p>Invalid &invalid; entity</p></body></html>",
            "empty_tags": "<html><head></head><body><p></p><a></a><img></body></html>",
            "deeply_nested": "<div>" * 1000 + "Content" + "</div>" * 1000,
            "special_chars": "<html><body><p>Special chars: <>&\"'</p></body></html>",
            "binary_content": "<html><body>\x00\x01\x02\x03</body></html>",
        }

    def test_malformed_html_processing(self, processor, malformed_html_samples):
        """Test processing of various malformed HTML samples."""
        for name, html in malformed_html_samples.items():
            # Should not raise exceptions
            content = processor.process_content(html, f"/test/{name}.html")
            assert isinstance(content, DocumentContent), f"Failed for {name}"
            assert content.encoding == "utf-8", f"Failed for {name}"

    def test_malformed_html_metadata_extraction(self, processor, malformed_html_samples):
        """Test metadata extraction from malformed HTML."""
        for name, html in malformed_html_samples.items():
            # Should not raise exceptions
            metadata = processor.extract_metadata(html, f"/test/{name}.html")
            assert isinstance(metadata, DocumentMetadata), f"Failed for {name}"
            assert metadata.content_type == "text/html", f"Failed for {name}"

    def test_malformed_html_link_extraction(self, processor, malformed_html_samples):
        """Test link extraction from malformed HTML."""
        for name, html in malformed_html_samples.items():
            # Should not raise exceptions
            links = processor.extract_links(html, "/test")
            assert isinstance(links, list), f"Failed for {name}"

    def test_empty_content_handling(self, processor):
        """Test handling of empty content."""
        empty_cases = ["", "   ", "\n\n\t", None]
        
        for empty_content in empty_cases:
            if empty_content is None:
                # Skip None case for process_content as it expects a string
                continue
                
            content = processor.process_content(empty_content, "/test/empty.html")
            assert isinstance(content, DocumentContent)
            assert content.content == empty_content
            
            metadata = processor.extract_metadata(empty_content, "/test/empty.html")
            assert isinstance(metadata, DocumentMetadata)
            
            links = processor.extract_links(empty_content, "/test")
            assert isinstance(links, list)
            assert len(links) == 0

    def test_none_content_handling(self, processor):
        """Test handling of None content."""
        # Should raise a validation error for None content
        with pytest.raises(Exception):  # Could be ValidationError or TypeError
            processor.process_content(None, "/test/none.html")

    def test_extremely_large_content(self, processor):
        """Test handling of extremely large HTML content."""
        # Create a very large HTML document
        large_html = "<html><body>"
        for i in range(10000):
            large_html += f"<p>Paragraph {i} with <a href='link{i}.html'>link {i}</a> and <img src='img{i}.jpg' alt='Image {i}'></p>"
        large_html += "</body></html>"
        
        # Should handle without issues (may take time but shouldn't crash)
        content = processor.process_content(large_html, "/test/large.html")
        assert isinstance(content, DocumentContent)
        
        metadata = processor.extract_metadata(large_html, "/test/large.html")
        assert isinstance(metadata, DocumentMetadata)
        
        # Link extraction might be slow but should work
        links = processor.extract_links(large_html, "/test")
        assert isinstance(links, list)
        assert len(links) == 20000  # 10000 links + 10000 images

    def test_invalid_unicode_content(self, processor):
        """Test handling of problematic Unicode content."""
        # Content with various encoding issues
        problematic_cases = [
            "Text with null bytes: \x00\x01\x02",
            "Mixed content: café test ñ",
            "Control characters: \x0b\x0c\x0e",
        ]
        
        for invalid_content in problematic_cases:
            try:
                # Should handle gracefully or raise specific exceptions
                content = processor.process_content(invalid_content, "/test/invalid.html")
                assert isinstance(content, DocumentContent)
                
                metadata = processor.extract_metadata(invalid_content, "/test/invalid.html")
                assert isinstance(metadata, DocumentMetadata)
            except (UnicodeEncodeError, UnicodeDecodeError):
                # These exceptions are acceptable for truly invalid Unicode
                pass

    def test_html_analyzer_parsing_failure(self, processor):
        """Test behavior when HTML parsing completely fails."""
        with patch('doc_ai_helper_backend.services.document.utils.html_analyzer.HTMLAnalyzer.parse_html_safely') as mock_parse:
            # Simulate parsing failure
            mock_parse.side_effect = Exception("Parsing failed")
            
            # Should handle the exception gracefully
            with pytest.raises(Exception):
                processor.extract_metadata("<html><body>Test</body></html>", "/test/fail.html")

    def test_beautifulsoup_import_failure(self, processor):
        """Test behavior when BeautifulSoup is not available."""
        # This is a hypothetical test - in reality BS4 is a dependency
        with patch('doc_ai_helper_backend.services.document.utils.html_analyzer.BeautifulSoup') as mock_bs:
            mock_bs.side_effect = ImportError("BeautifulSoup not available")
            
            # Should handle import error gracefully in parse_html_safely
            with pytest.raises(ImportError):
                processor.extract_metadata("<html><body>Test</body></html>", "/test/no_bs.html")

    def test_transform_links_with_invalid_params(self, processor):
        """Test link transformation with invalid parameters."""
        html = "<html><body><a href='test.html'>Link</a></body></html>"
        
        # Test with None service
        result = processor.transform_links(html, "/test/doc.html", "https://api.example.com")
        assert isinstance(result, str)
        
        # Test with invalid service
        result = processor.transform_links(
            html, "/test/doc.html", "https://api.example.com",
            service="invalid", owner="test", repo="test", ref="main"
        )
        assert isinstance(result, str)
        
        # Test with missing parameters
        result = processor.transform_links(
            html, "/test/doc.html", "https://api.example.com",
            service="github"  # Missing owner, repo, ref
        )
        assert isinstance(result, str)

    def test_invalid_path_handling(self, processor):
        """Test handling of invalid file paths."""
        html = "<html><body><a href='../../../dangerous/path'>Link</a></body></html>"
        
        # Should handle path traversal attempts safely
        links = processor.extract_links(html, "/test")
        assert len(links) == 1
        assert links[0].url == "../../../dangerous/path"
        
        # Transform should handle safely
        result = processor.transform_links(html, "/test/doc.html", "https://api.example.com")
        assert isinstance(result, str)

    def test_circular_reference_handling(self, processor):
        """Test handling of potential circular references in HTML."""
        html = """
        <html>
        <body>
            <a href="#self">Self reference</a>
            <a href="">Empty href</a>
            <a href=".">Current directory</a>
            <a href="..">Parent directory</a>
        </body>
        </html>
        """
        
        links = processor.extract_links(html, "/test")
        assert len(links) == 4
        
        # Should handle all types of references
        hrefs = [link.url for link in links]
        assert "#self" in hrefs
        assert "" in hrefs
        assert "." in hrefs
        assert ".." in hrefs

    def test_memory_stress_with_repeated_operations(self, processor):
        """Test memory usage with repeated operations."""
        html = "<html><body><h1>Test</h1><p>Content</p></body></html>"
        
        # Perform many operations to check for memory leaks
        for i in range(100):
            content = processor.process_content(html, f"/test/doc{i}.html")
            metadata = processor.extract_metadata(html, f"/test/doc{i}.html")
            links = processor.extract_links(html, "/test")
            
            # Basic assertions to ensure functionality
            assert isinstance(content, DocumentContent)
            assert isinstance(metadata, DocumentMetadata)
            assert isinstance(links, list)

    def test_concurrent_access_simulation(self, processor):
        """Test behavior under simulated concurrent access."""
        import threading
        import time
        
        html = "<html><body><h1>Concurrent Test</h1></body></html>"
        results = []
        errors = []
        
        def process_html():
            try:
                content = processor.process_content(html, "/test/concurrent.html")
                metadata = processor.extract_metadata(html, "/test/concurrent.html")
                results.append((content, metadata))
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=process_html)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5)  # 5 second timeout per thread
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10, f"Expected 10 results, got {len(results)}"

    def test_logging_behavior_on_errors(self, processor, caplog):
        """Test that appropriate logging occurs on errors."""
        with caplog.at_level(logging.WARNING):
            # Test with problematic HTML that might cause warnings
            problematic_html = "<html><body><script>alert('test')</script></body></html>"
            
            processor.extract_metadata(problematic_html, "/test/problematic.html")
            
            # Check if any warnings were logged (implementation dependent)
            # This test is more about ensuring logging doesn't crash than specific messages

    def test_edge_case_link_urls(self, processor):
        """Test handling of edge case link URLs."""
        edge_case_html = """
        <html>
        <body>
            <a href="javascript:void(0)">JavaScript link</a>
            <a href="data:text/html,<h1>Data URL</h1>">Data URL</a>
            <a href="tel:+1234567890">Phone link</a>
            <a href="mailto:test@example.com?subject=Test">Email with params</a>
            <a href="ftp://files.example.com/file.zip">FTP link</a>
            <a href="//example.com/protocol-relative">Protocol relative</a>
            <a href="http://localhost:8080/local">Local server</a>
            <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" alt="Base64 image">
        </body>
        </html>
        """
        
        links = processor.extract_links(edge_case_html, "/test")
        assert len(links) >= 8  # All links should be extracted
        
        # Check that various URL schemes are handled
        urls = [link.url for link in links]
        assert any("javascript:" in url for url in urls)
        assert any("data:" in url for url in urls)
        assert any("tel:" in url for url in urls)
        assert any("mailto:" in url for url in urls)
        assert any("ftp:" in url for url in urls)

    def test_transform_links_network_simulation(self, processor):
        """Test link transformation under simulated network conditions."""
        html = "<html><body><a href='test.html'>Link</a><img src='image.jpg'></body></html>"
        
        # Simulate configuration not available
        with patch("doc_ai_helper_backend.core.config.settings.forgejo_base_url", None):
            result = processor.transform_links(
                html, "/test/doc.html", "https://api.example.com",
                service="forgejo", owner="test", repo="test", ref="main"
            )
            assert isinstance(result, str)
            # Should fall back to API URLs when Forgejo config is unavailable

    @pytest.mark.parametrize("invalid_html", [
        "<html><script>while(true){}</script></html>",  # Infinite loop in script
        "<html>" + "x" * 1000000 + "</html>",  # Very long text node
        "<html><body>" + "<div>" * 10000 + "</div>" * 10000 + "</body></html>",  # Deep nesting
    ])
    def test_problematic_html_patterns(self, processor, invalid_html):
        """Test handling of potentially problematic HTML patterns."""
        # Should handle without hanging or crashing
        content = processor.process_content(invalid_html, "/test/problematic.html")
        assert isinstance(content, DocumentContent)
        
        metadata = processor.extract_metadata(invalid_html, "/test/problematic.html")
        assert isinstance(metadata, DocumentMetadata)

    def test_resource_cleanup(self, processor):
        """Test that resources are properly cleaned up."""
        html = "<html><body><h1>Test</h1></body></html>"
        
        # Process multiple times and check that no resources leak
        initial_refs = len(processor.__dict__) if hasattr(processor, '__dict__') else 0
        
        for i in range(50):
            processor.process_content(html, f"/test/cleanup{i}.html")
            processor.extract_metadata(html, f"/test/cleanup{i}.html")
            processor.extract_links(html, "/test")
        
        # Object should not accumulate state
        final_refs = len(processor.__dict__) if hasattr(processor, '__dict__') else 0
        assert final_refs == initial_refs, "Processor accumulated state between calls"