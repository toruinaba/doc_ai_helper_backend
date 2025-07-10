"""
Test for Git service mock data functionality.

This module contains unit tests for the mock data used in MockGitService.
"""

import pytest

from doc_ai_helper_backend.services.git.mock_data import (
    MARKDOWN_WITH_FRONTMATTER,
    MARKDOWN_WITH_LINKS,
)


class TestMockData:
    """Test the mock data functionality."""

    def test_markdown_with_frontmatter_exists(self):
        """Test that MARKDOWN_WITH_FRONTMATTER exists and is a string."""
        assert isinstance(MARKDOWN_WITH_FRONTMATTER, str)
        assert len(MARKDOWN_WITH_FRONTMATTER) > 0

    def test_markdown_with_links_exists(self):
        """Test that MARKDOWN_WITH_LINKS exists and is a string."""
        assert isinstance(MARKDOWN_WITH_LINKS, str)
        assert len(MARKDOWN_WITH_LINKS) > 0

    def test_mock_data_basic_structure(self):
        """Test basic structure of mock data."""
        # Test that constants are non-empty strings
        assert MARKDOWN_WITH_FRONTMATTER.strip() != ""
        assert MARKDOWN_WITH_LINKS.strip() != ""
