"""
Tests for document processing tools.
"""

import pytest
import json

from doc_ai_helper_backend.services.mcp.tools.document_tools import (
    extract_document_context,
    analyze_document_structure,
    optimize_document_content,
)


class TestDocumentTools:
    """Tests for document processing tools."""

    @pytest.fixture
    def sample_markdown_content(self):
        """Sample markdown content for testing."""
        return """# Main Title

## Introduction

This is an introduction section with some content.

## Features

- Feature 1
- Feature 2  
- Feature 3

### Code Example

```python
def hello():
    print("Hello, World!")
```

## Conclusion

This concludes the document.

![Image](image.png)
[Link](https://example.com)
"""

    @pytest.mark.asyncio
    async def test_extract_document_context_basic(self):
        """Test basic document context extraction."""
        content = "# Test Title\n\nSome content here."

        result = await extract_document_context(
            document_content=content,
            title="Test Document",
            path="/docs/test.md",
            repository="owner/repo",
        )

        assert isinstance(result, str)
        result_dict = json.loads(result)
        assert result_dict["title"] == "Test Document"
        assert result_dict["content"] == content
        assert result_dict["path"] == "/docs/test.md"
        assert result_dict["repository"] == "owner/repo"
        assert "analysis" in result_dict

    @pytest.mark.asyncio
    async def test_extract_document_context_with_analysis(
        self, sample_markdown_content
    ):
        """Test document context extraction with detailed analysis."""
        result = await extract_document_context(
            document_content=sample_markdown_content, title="Sample Document"
        )

        assert isinstance(result, str)
        result_dict = json.loads(result)
        analysis = result_dict["analysis"]
        assert analysis["word_count"] > 0
        assert analysis["line_count"] > 0
        assert len(analysis["headings"]) > 0
        assert analysis["has_code_blocks"] is True
        assert analysis["has_links"] is True
        assert analysis["has_images"] is True

    @pytest.mark.asyncio
    async def test_extract_document_context_empty_content(self):
        """Test context extraction with empty content."""
        result = await extract_document_context(
            document_content="", title="Empty Document"
        )

        assert isinstance(result, str)
        result_dict = json.loads(result)
        assert result_dict["title"] == "Empty Document"
        assert result_dict["content"] == ""
        assert result_dict["analysis"]["word_count"] == 0

    @pytest.mark.asyncio
    async def test_analyze_document_structure_with_headings(
        self, sample_markdown_content
    ):
        """Test document structure analysis with various headings."""
        result = await analyze_document_structure(sample_markdown_content)

        assert isinstance(result, dict)
        assert "heading_levels" in result
        assert "total_headings" in result
        assert "code_blocks" in result
        assert "structure_quality" in result
        assert "recommendations" in result

        # Check heading levels detection
        heading_levels = result["heading_levels"]
        assert 1 in heading_levels  # # Main Title
        assert 2 in heading_levels  # ## Introduction, ## Features, ## Conclusion
        assert 3 in heading_levels  # ### Code Example

    @pytest.mark.asyncio
    async def test_analyze_document_structure_empty(self):
        """Test structure analysis with empty content."""
        result = await analyze_document_structure("")

        assert result["total_headings"] == 0
        assert result["code_blocks"] == 0
        assert result["lists"] == 0

    @pytest.mark.asyncio
    async def test_analyze_document_structure_recommendations(self):
        """Test that structure analysis provides recommendations."""
        # Content without proper structure
        poor_content = "Some text without headings or structure."

        result = await analyze_document_structure(poor_content)

        recommendations = result["recommendations"]
        assert isinstance(recommendations, list)
        assert any("title" in rec.lower() for rec in recommendations)

    @pytest.mark.asyncio
    async def test_optimize_document_content_readability(self, sample_markdown_content):
        """Test content optimization for readability."""
        result = await optimize_document_content(
            document_content=sample_markdown_content, optimization_type="readability"
        )

        assert isinstance(result, str)
        result_dict = json.loads(result)
        assert result_dict["optimization_type"] == "readability"
        assert "suggestions" in result_dict
        assert "original_content" in result_dict
        assert "priority" in result_dict

    @pytest.mark.asyncio
    async def test_optimize_document_content_structure(self, sample_markdown_content):
        """Test content optimization for structure."""
        result = await optimize_document_content(
            document_content=sample_markdown_content, optimization_type="structure"
        )

        assert isinstance(result, str)
        result_dict = json.loads(result)
        assert result_dict["optimization_type"] == "structure"
        assert isinstance(result_dict["suggestions"], list)

    @pytest.mark.asyncio
    async def test_optimize_document_content_seo(self, sample_markdown_content):
        """Test content optimization for SEO."""
        result = await optimize_document_content(
            document_content=sample_markdown_content, optimization_type="seo"
        )

        assert isinstance(result, str)
        result_dict = json.loads(result)
        assert result_dict["optimization_type"] == "seo"
        assert isinstance(result_dict["suggestions"], list)

    @pytest.mark.asyncio
    async def test_optimize_document_content_unknown_type(
        self, sample_markdown_content
    ):
        """Test content optimization with unknown optimization type."""
        result = await optimize_document_content(
            document_content=sample_markdown_content, optimization_type="unknown"
        )

        assert isinstance(result, str)
        result_dict = json.loads(result)
        assert result_dict["optimization_type"] == "unknown"
        assert "Unknown optimization type" in result_dict["suggestions"]

    @pytest.mark.asyncio
    async def test_extract_document_context_error_handling(self):
        """Test error handling in document context extraction."""
        # Test with empty string instead of None
        result = await extract_document_context(document_content="", title="Test")

        # Should handle gracefully
        assert isinstance(result, str)
        result_dict = json.loads(result)
        assert result_dict["title"] == "Test"

    @pytest.mark.asyncio
    async def test_analyze_document_structure_with_lists(self):
        """Test structure analysis detects lists correctly."""
        content_with_lists = """# Title

- Item 1
- Item 2
* Item 3  
+ Item 4

Some text.
"""

        result = await analyze_document_structure(content_with_lists)

        assert result["lists"] > 0  # Should detect list items

    @pytest.mark.asyncio
    async def test_analyze_document_structure_code_blocks(self):
        """Test structure analysis detects code blocks correctly."""
        content_with_code = """# Title

```python
def test():
    pass
```

```javascript
console.log("test");
```

Some text.
"""

        result = await analyze_document_structure(content_with_code)

        assert result["code_blocks"] == 2  # Should detect 2 code blocks
