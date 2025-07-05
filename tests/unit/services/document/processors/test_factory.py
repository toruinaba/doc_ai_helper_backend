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
from doc_ai_helper_backend.models.document import DocumentType
from doc_ai_helper_backend.core.exceptions import DocumentParsingException


class TestDocumentProcessorFactory:
    """Test the document processor factory."""

    def test_factory_has_processors(self):
        """Test that factory has processor registry."""
        assert hasattr(DocumentProcessorFactory, "_processors")
        assert isinstance(DocumentProcessorFactory._processors, dict)

    def test_create_markdown_processor(self):
        """Test creating a markdown processor."""
        processor = DocumentProcessorFactory.create(DocumentType.MARKDOWN)

        assert processor is not None
        assert isinstance(processor, MarkdownProcessor)
        assert isinstance(processor, DocumentProcessorBase)

    def test_create_html_processor(self):
        """Test creating an HTML processor."""
        processor = DocumentProcessorFactory.create(DocumentType.HTML)

        assert processor is not None
        assert isinstance(processor, HTMLProcessor)
        assert isinstance(processor, DocumentProcessorBase)

    def test_unsupported_document_type(self):
        """Test handling of unsupported document types."""

        # Create a mock DocumentType that doesn't exist in the registry
        class UnsupportedType:
            def __str__(self):
                return "UNSUPPORTED"

        with pytest.raises(DocumentParsingException) as exc_info:
            DocumentProcessorFactory.create(UnsupportedType())

        assert "unsupported" in str(exc_info.value).lower()

    def test_processor_singleton_behavior(self):
        """Test that processors are created fresh each time (not singleton)."""
        processor1 = DocumentProcessorFactory.create(DocumentType.MARKDOWN)
        processor2 = DocumentProcessorFactory.create(DocumentType.MARKDOWN)

        # Should be different instances but same type
        assert type(processor1) == type(processor2)
        assert processor1 is not processor2

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
            # Create a mock document type
            class TestDocumentType:
                def __str__(self):
                    return "TEST"

            original_processors = DocumentProcessorFactory._processors.copy()

            try:
                test_type = TestDocumentType()
                DocumentProcessorFactory.register(test_type, TestProcessor)

                # Verify registration
                processor = DocumentProcessorFactory.create(test_type)
                assert isinstance(processor, TestProcessor)

            finally:
                # Restore original processors
                DocumentProcessorFactory._processors = original_processors

    def test_factory_methods_exist(self):
        """Test that factory has required methods."""
        assert hasattr(DocumentProcessorFactory, "create")
        assert callable(DocumentProcessorFactory.create)

        # Check for optional methods
        optional_methods = ["register", "get_supported_types", "list_processors"]
        for method in optional_methods:
            if hasattr(DocumentProcessorFactory, method):
                assert callable(getattr(DocumentProcessorFactory, method))
