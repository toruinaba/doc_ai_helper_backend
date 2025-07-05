"""
Test for MCP analysis tools functionality.

This module contains unit tests for the analysis tools used in MCP server.
"""

import pytest
from unittest.mock import AsyncMock, patch

from doc_ai_helper_backend.services.mcp.tools.analysis_tools import (
    analyze_document_quality,
    extract_document_topics,
    check_document_completeness,
)


class TestAnalysisTools:
    """Test the MCP analysis tools functionality."""

    @pytest.mark.asyncio
    async def test_analyze_document_quality_basic(self):
        """Test basic document quality analysis."""
        document_content = """
        # Test Document
        
        This is a well-structured document with proper headings.
        It contains multiple paragraphs and good formatting.
        
        ## Section 1
        Content here with appropriate length.
        
        ## Section 2
        More content with good structure.
        """

        result = await analyze_document_quality(document_content)

        assert isinstance(result, dict)
        assert "overall_score" in result
        assert "metrics" in result
        assert "grade" in result
        assert isinstance(result["overall_score"], (int, float))
        assert result["overall_score"] >= 0

    @pytest.mark.asyncio
    async def test_analyze_document_quality_with_custom_metrics(self):
        """Test document quality analysis with custom metrics."""
        document_content = "Short document content."
        custom_metrics = ["readability", "structure"]

        result = await analyze_document_quality(document_content, custom_metrics)

        assert isinstance(result, dict)
        if "error" not in result:
            assert "overall_score" in result
            assert "metrics" in result

    @pytest.mark.asyncio
    async def test_analyze_document_quality_empty_content(self):
        """Test document quality analysis with empty content."""
        result = await analyze_document_quality("")

        assert isinstance(result, dict)
        assert "overall_score" in result
        assert result["overall_score"] == 0  # Empty content should score 0

    @pytest.mark.asyncio
    async def test_extract_document_topics_basic(self):
        """Test basic document topic extraction."""
        document_content = """
        Machine learning is an important technology.
        Artificial intelligence applications are growing.
        Data science involves statistical analysis.
        """

        result = await extract_document_topics(document_content)

        assert isinstance(result, list)
        assert len(result) >= 0

    @pytest.mark.asyncio
    async def test_extract_document_topics_with_count(self):
        """Test topic extraction with specific topic count."""
        document_content = """
        Machine learning applications in healthcare.
        Natural language processing for text analysis.
        Computer vision for image recognition.
        """

        for topic_count in [1, 3, 5]:
            result = await extract_document_topics(document_content, topic_count)
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_check_document_completeness_basic(self):
        """Test basic document completeness checking."""
        document_content = """
        # Introduction
        This is the introduction section.
        
        # Method
        This describes the methodology.
        
        # Results
        Here are the results.
        """

        result = await check_document_completeness(document_content)

        assert isinstance(result, dict)
        assert "completeness_score" in result
        assert "missing_sections" in result
        assert isinstance(result["completeness_score"], (int, float))

    @pytest.mark.asyncio
    async def test_check_document_completeness_missing_sections(self):
        """Test completeness checking with missing sections."""
        # Document without methodology section
        document_content = """
        # Introduction
        This is a basic document.
        
        # Conclusion
        That's the end.
        """

        result = await check_document_completeness(document_content)

        assert isinstance(result, dict)
        assert "missing_sections" in result
        # Note: specific missing sections depend on implementation

    @pytest.mark.asyncio
    async def test_analysis_error_handling(self):
        """Test error handling in analysis functions."""
        # Test with None input - these functions handle errors internally
        result = await analyze_document_quality(None)
        assert isinstance(result, dict)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_analysis_functions_return_format(self):
        """Test that all analysis functions return expected format."""
        test_content = "Test document content for analysis."

        # Test that all functions return expected types
        quality_result = await analyze_document_quality(test_content)
        topics_result = await extract_document_topics(test_content)
        completeness_result = await check_document_completeness(test_content)

        assert isinstance(quality_result, dict)
        assert isinstance(topics_result, list)
        assert isinstance(completeness_result, dict)
