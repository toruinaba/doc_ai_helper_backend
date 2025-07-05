"""
Unit tests for document processor base classes.

This module tests the abstract base processor that all document processors inherit from.
"""

import pytest
from abc import ABC

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
        return DocumentContent(
            raw=content, processed=f"processed: {content}", type=DocumentType.MARKDOWN
        )

    def extract_metadata(self, content: str, path: str, **kwargs) -> DocumentMetadata:
        """Extract metadata from document - test implementation."""
        return DocumentMetadata(
            title=f"Title from {path}",
            description="Test description",
            author="Test Author",
            created_at=None,
            updated_at=None,
            tags=[],
            custom_fields={},
        )

    def can_process(self, file_path: str) -> bool:
        """Check if processor can handle the file - test implementation."""
        return file_path.endswith(".test")


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
        assert result.raw == content
        assert result.processed == f"processed: {content}"
        assert result.type == DocumentType.MARKDOWN

    def test_extract_metadata(self, processor):
        """Test the extract_metadata method."""
        content = "Test content"
        path = "test.test"

        result = processor.extract_metadata(content, path)

        assert isinstance(result, DocumentMetadata)
        assert result.title == f"Title from {path}"
        assert result.description == "Test description"
        assert result.author == "Test Author"
        assert result.tags == []
        assert result.custom_fields == {}

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
