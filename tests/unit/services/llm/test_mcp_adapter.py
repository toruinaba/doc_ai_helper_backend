"""
Tests for the MCP adapter.
"""

import pytest
from unittest.mock import MagicMock

from doc_ai_helper_backend.services.llm.mcp_adapter import MCPAdapter
from doc_ai_helper_backend.models.document import DocumentType
from doc_ai_helper_backend.models.link_info import LinkInfo


class TestMCPAdapter:
    """Tests for the MCPAdapter."""

    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing."""
        # Create a mock document without using the actual class structure
        doc = MagicMock()
        doc.path = "example/docs/file.md"
        doc.name = "file.md"
        doc.type = DocumentType.MARKDOWN
        doc.content = MagicMock()
        doc.content.text = "# Sample Document\n\nThis is a sample document."
        doc.metadata = MagicMock()
        doc.metadata.title = "Sample Document"
        doc.metadata.frontmatter = {
            "title": "Sample Document",
            "tags": ["test", "sample"],
        }
        doc.owner = "example"
        doc.repository = "docs-project"
        doc.service = "github"
        doc.ref = "main"
        doc.links = [
            LinkInfo(
                text="Internal Link",
                url="other-file.md",
                is_image=False,
                position=(50, 70),
                is_external=False,
            ),
            LinkInfo(
                text="External Link",
                url="https://example.com",
                is_image=False,
                position=(100, 120),
                is_external=True,
            ),
        ]
        return doc

    def test_convert_document_to_context(self, sample_document):
        """Test converting a document to MCP context."""
        context = MCPAdapter.convert_document_to_context(sample_document)

        # Check basic structure
        assert context["type"] == "document"
        assert context["content"] == sample_document.content.text

        # Check metadata
        assert context["metadata"]["title"] == "Sample Document"
        assert context["metadata"]["path"] == "example/docs/file.md"
        assert context["metadata"]["repository"] == "example/docs-project"
        assert context["metadata"]["service"] == "github"
        assert context["metadata"]["format"] == "markdown"

        # Check frontmatter
        assert "frontmatter" in context["metadata"]
        assert context["metadata"]["frontmatter"]["tags"] == ["test", "sample"]

        # Check links
        assert len(context["links"]) == 2
        assert context["links"][0]["text"] == "Internal Link"
        assert context["links"][0]["url"] == "other-file.md"
        assert context["links"][0]["is_external"] == False
        assert context["links"][1]["text"] == "External Link"
        assert context["links"][1]["url"] == "https://example.com"
        assert context["links"][1]["is_external"] == True

    def test_optimize_context(self):
        """Test context optimization."""
        # Create sample contexts
        contexts = [
            {
                "type": "document",
                "content": "A" * 1000,  # Large content
                "metadata": {"title": "Doc 1"},
            },
            {
                "type": "document",
                "content": "B" * 1000,  # Large content
                "metadata": {"title": "Doc 2"},
            },
        ]

        # Test with enough tokens
        optimized = MCPAdapter.optimize_context(contexts, 10000)
        assert len(optimized) == 2
        assert len(optimized[0]["content"]) == 1000
        assert len(optimized[1]["content"]) == 1000

        # Test with limited tokens
        optimized = MCPAdapter.optimize_context(contexts, 300)
        assert len(optimized) == 2
        assert len(optimized[0]["content"]) < 1000
        assert len(optimized[1]["content"]) < 1000

        # Test with current prompt tokens
        optimized = MCPAdapter.optimize_context(
            contexts, 1000, current_prompt_tokens=500
        )
        assert len(optimized) == 2
        assert len(optimized[0]["content"]) < 1000
        assert len(optimized[1]["content"]) < 1000
