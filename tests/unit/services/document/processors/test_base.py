"""
Unit tests for document processor base classes.

This module tests the abstract base processor that all document processors inherit from.
"""

import pytest
from abc import ABC
from typing import List

from datetime import datetime

from doc_ai_helper_backend.services.document.processors.base import (
    DocumentProcessorBase,
)
from doc_ai_helper_backend.models.document import (
    DocumentContent,
    DocumentMetadata,
    DocumentType,
)


class ConcreteDocumentProcessor(DocumentProcessorBase):
    """Concrete implementation of DocumentProcessorBase for testing."""

    def process_content(self, content: str, path: str, **kwargs) -> DocumentContent:
        """Process document content - test implementation."""
        return DocumentContent(content=f"processed: {content}", encoding="utf-8")

    def extract_metadata(self, content: str, path: str, **kwargs) -> DocumentMetadata:
        """Extract metadata from document - test implementation."""
        return DocumentMetadata(
            size=len(content),
            last_modified=datetime.now(),
            content_type="text/plain",
            sha="test-sha",
            extra={"test": True},
        )

    def can_process(self, file_path: str) -> bool:
        """Check if processor can handle the file - test implementation."""
        return file_path.endswith(".test")

    def extract_links(self, content: str, path: str) -> List:
        """Extract links from document - test implementation."""
        # Simple mock implementation - just return empty list
        return []

    def transform_links(self, content: str, path: str, base_url: str) -> str:
        """Transform links in document - test implementation."""
        # Simple mock implementation - just return content as-is
        return content


class TestDocumentProcessorBase:
    """Test the document processor base class."""

    @pytest.fixture
    def processor(self):
        """Create a concrete processor instance for testing."""
        return ConcreteDocumentProcessor()

    def test_abstract_nature(self):
        """Test that DocumentProcessorBase is abstract."""
        assert issubclass(DocumentProcessorBase, ABC)

        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            DocumentProcessorBase()

    def test_concrete_implementation(self, processor):
        """Test that concrete implementation works correctly."""
        assert processor is not None
        assert isinstance(processor, DocumentProcessorBase)
        assert isinstance(processor, ConcreteDocumentProcessor)

    def test_process_content(self, processor):
        """Test the process_content method."""
        content = "Test content"
        path = "test.test"

        result = processor.process_content(content, path)

        assert isinstance(result, DocumentContent)
        assert result.content == f"processed: {content}"
        assert result.encoding == "utf-8"

    def test_extract_metadata(self, processor):
        """Test the extract_metadata method."""
        content = "Test content"
        path = "test.test"

        result = processor.extract_metadata(content, path)

        assert isinstance(result, DocumentMetadata)
        assert result.size == len(content)
        assert result.content_type == "text/plain"
        assert result.sha == "test-sha"
        assert result.extra == {"test": True}

    def test_can_process(self, processor):
        """Test the can_process method."""
        assert processor.can_process("file.test") is True
        assert processor.can_process("file.md") is False
        assert processor.can_process("file.html") is False

    def test_interface_coverage(self, processor):
        """Test that all required methods are implemented."""
        # Check that all abstract methods are implemented
        required_methods = ["process_content", "extract_metadata", "can_process"]

        for method_name in required_methods:
            assert hasattr(processor, method_name)
            assert callable(getattr(processor, method_name))
