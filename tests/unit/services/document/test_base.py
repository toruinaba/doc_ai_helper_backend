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
            content=content,
            encoding="utf-8"
        )

    def extract_metadata(self, content: str, path: str, **kwargs) -> DocumentMetadata:
        """Extract metadata from document - test implementation."""
        from datetime import datetime
        return DocumentMetadata(
            size=len(content),
            last_modified=datetime.now(),
            content_type="text/plain",
            sha="test_sha",
            extra={"test": "data"}
        )

    def extract_links(self, content: str, path: str, **kwargs) -> list:
        """Extract links from document - test implementation."""
        # Simple test implementation - look for markdown links
        import re

        links = []
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        matches = re.findall(link_pattern, content)
        for text, url in matches:
            links.append(
                {
                    "text": text,
                    "url": url,
                    "is_image": False,
                    "is_external": url.startswith(("http://", "https://")),
                }
            )
        return links

    def transform_links(
        self, content: str, path: str, base_url: str, **kwargs
    ) -> str:
        """Transform links in document - test implementation."""
        # Simple test implementation - replace relative links
        import re

        def replace_link(match):
            text = match.group(1)
            url = match.group(2)
            if not url.startswith(("http://", "https://", "mailto:", "#")):
                # Relative link - make it absolute
                if base_url.endswith("/"):
                    new_url = f"{base_url}{url}"
                else:
                    new_url = f"{base_url}/{url}"
                return f"[{text}]({new_url})"
            return match.group(0)

        return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_link, content)

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
        assert result.content == content
        assert result.encoding == "utf-8"

    def test_extract_metadata(self, processor):
        """Test the extract_metadata method."""
        content = "Test content"
        path = "test.test"

        result = processor.extract_metadata(content, path)

        assert isinstance(result, DocumentMetadata)
        assert result.size == len(content)
        assert result.content_type == "text/plain"
        assert result.sha == "test_sha"
        assert result.extra == {"test": "data"}

    def test_extract_links(self, processor):
        """Test the extract_links method."""
        content = "Test content with a link [example](http://example.com)"
        path = "test.test"

        result = processor.extract_links(content, path)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["text"] == "example"
        assert result[0]["url"] == "http://example.com"
        assert result[0]["is_image"] is False
        assert result[0]["is_external"] is True

    def test_transform_links(self, processor):
        """Test the transform_links method."""
        content = "Test content with a link [example](relative/path)"
        path = "test.test"
        base_url = "http://base.url"

        result = processor.transform_links(content, path, base_url)

        assert isinstance(result, str)
        assert (
            result
            == "Test content with a link [example](http://base.url/relative/path)"
        )

    def test_can_process(self, processor):
        """Test the can_process method."""
        assert processor.can_process("file.test") is True
        assert processor.can_process("file.md") is False
        assert processor.can_process("file.html") is False

    def test_interface_coverage(self, processor):
        """Test that all required methods are implemented."""
        # Check that all abstract methods are implemented
        required_methods = [
            "process_content",
            "extract_metadata",
            "extract_links",
            "transform_links",
            "can_process",
        ]

        for method_name in required_methods:
            assert hasattr(processor, method_name)
            assert callable(getattr(processor, method_name))
