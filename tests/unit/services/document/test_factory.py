"""
Unit tests for document processor factory.

This module tests the factory that creates appropriate document processors based on file type.
"""

import pytest
from unittest.mock import patch, MagicMock

from doc_ai_helper_backend.services.document.processors.factory import (
    DocumentProcessorFactory,
)
from doc_ai_helper_backend.services.document.processors.base import (
    DocumentProcessorBase,
)
from doc_ai_helper_backend.services.document.processors.markdown import (
    MarkdownProcessor,
)
from doc_ai_helper_backend.services.document.processors.html import HTMLProcessor
from doc_ai_helper_backend.core.exceptions import DocumentParsingException


class TestDocumentProcessorFactory:
    """Test the document processor factory."""

    def test_factory_has_processors(self):
        """Test that factory has processor registry."""
        assert hasattr(DocumentProcessorFactory, "_processors")
        assert isinstance(DocumentProcessorFactory._processors, dict)

    def test_create_markdown_processor(self):
        """Test creating a markdown processor."""
        processor = DocumentProcessorFactory.create("test.md")

        assert processor is not None
        assert isinstance(processor, MarkdownProcessor)
        assert isinstance(processor, DocumentProcessorBase)

    def test_create_html_processor(self):
        """Test creating an HTML processor."""
        processor = DocumentProcessorFactory.create("test.html")

        assert processor is not None
        assert isinstance(processor, HTMLProcessor)
        assert isinstance(processor, DocumentProcessorBase)

    def test_create_markdown_extensions(self):
        """Test creating processors for various markdown extensions."""
        markdown_extensions = [".md", ".markdown", ".mdown", ".mkd"]

        for ext in markdown_extensions:
            processor = DocumentProcessorFactory.create(f"test{ext}")
            assert isinstance(processor, MarkdownProcessor)

    def test_create_html_extensions(self):
        """Test creating processors for various HTML extensions."""
        html_extensions = [".html", ".htm"]

        for ext in html_extensions:
            processor = DocumentProcessorFactory.create(f"test{ext}")
            assert isinstance(processor, HTMLProcessor)

    def test_case_insensitive_extension(self):
        """Test that extension matching is case insensitive."""
        processor_lower = DocumentProcessorFactory.create("test.md")
        processor_upper = DocumentProcessorFactory.create("test.MD")
        processor_mixed = DocumentProcessorFactory.create("test.Md")

        assert type(processor_lower) == type(processor_upper) == type(processor_mixed)
        assert all(
            isinstance(p, MarkdownProcessor)
            for p in [processor_lower, processor_upper, processor_mixed]
        )

    def test_unsupported_file_type(self):
        """Test handling of unsupported file types."""
        with pytest.raises(DocumentParsingException) as exc_info:
            DocumentProcessorFactory.create("test.txt")

        assert "test.txt" in str(exc_info.value)
        assert "unsupported" in str(exc_info.value).lower()

    def test_file_without_extension(self):
        """Test handling of files without extensions."""
        with pytest.raises(DocumentParsingException):
            DocumentProcessorFactory.create("README")

    def test_empty_filename(self):
        """Test handling of empty filename."""
        with pytest.raises(DocumentParsingException):
            DocumentProcessorFactory.create("")

    def test_none_filename(self):
        """Test handling of None filename."""
        with pytest.raises((DocumentParsingException, AttributeError)):
            DocumentProcessorFactory.create(None)

    def test_register_new_processor(self):
        """Test registering a new processor type."""

        # Create a mock processor class
        class TestProcessor(DocumentProcessorBase):
            def process_content(self, content, path, **kwargs):
                pass

            def extract_metadata(self, content, path, **kwargs):
                pass

            def can_process(self, file_path):
                return True

        # Test registration if the method exists
        if hasattr(DocumentProcessorFactory, "register"):
            original_processors = DocumentProcessorFactory._processors.copy()

            try:
                DocumentProcessorFactory.register(".test", TestProcessor)

                # Verify registration
                processor = DocumentProcessorFactory.create("file.test")
                assert isinstance(processor, TestProcessor)

            finally:
                # Restore original processors
                DocumentProcessorFactory._processors = original_processors

    def test_processor_singleton_behavior(self):
        """Test that processors are created fresh each time (not singleton)."""
        processor1 = DocumentProcessorFactory.create("test.md")
        processor2 = DocumentProcessorFactory.create("test.md")

        # Should be different instances but same type
        assert type(processor1) == type(processor2)
        assert processor1 is not processor2

    def test_factory_methods_exist(self):
        """Test that factory has required methods."""
        assert hasattr(DocumentProcessorFactory, "create")
        assert callable(DocumentProcessorFactory.create)

        # Check for optional methods
        optional_methods = ["register", "get_supported_extensions", "list_processors"]
        for method in optional_methods:
            if hasattr(DocumentProcessorFactory, method):
                assert callable(getattr(DocumentProcessorFactory, method))
