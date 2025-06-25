"""
Updated tests for SystemPromptBuilder with context-aware functionality.

This module contains updated unit tests for the SystemPromptBuilder and JapaneseSystemPromptBuilder
that match the current implementation.
"""

import pytest
import time
from unittest.mock import patch, MagicMock

from doc_ai_helper_backend.services.llm.system_prompt_builder import (
    SystemPromptBuilder,
    JapaneseSystemPromptBuilder,
    SystemPromptCache,
)
from doc_ai_helper_backend.models.repository_context import (
    RepositoryContext,
    DocumentMetadata,
    GitService,
    DocumentType,
)


class TestSystemPromptCache:
    """Test SystemPromptCache functionality."""

    def test_cache_initialization(self):
        """Test cache initialization."""
        cache = SystemPromptCache(ttl_seconds=1800)
        assert cache.ttl_seconds == 1800
        assert len(cache.cache) == 0
        assert len(cache.cache_times) == 0

    def test_cache_set_and_get(self):
        """Test setting and getting cached values."""
        cache = SystemPromptCache()

        # Set a value
        cache.set("test_key", "test_value")

        # Get the value
        result = cache.get("test_key")
        assert result == "test_value"

    def test_cache_expiration(self):
        """Test cache expiration functionality."""
        cache = SystemPromptCache(ttl_seconds=1)

        # Set a value
        cache.set("test_key", "test_value")

        # Should be available immediately
        assert cache.get("test_key") == "test_value"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired now
        assert cache.get("test_key") is None

    def test_cache_miss(self):
        """Test cache miss behavior."""
        cache = SystemPromptCache()

        # Non-existent key should return None
        assert cache.get("non_existent") is None

    def test_cache_clear(self):
        """Test cache clearing."""
        cache = SystemPromptCache()

        # Add some items
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Clear cache
        cache.clear()

        # Should be empty
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = SystemPromptCache(ttl_seconds=3600)

        # Add some items
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        stats = cache.get_stats()
        assert stats["total_items"] == 2
        assert stats["valid_items"] == 2
        assert stats["expired_items"] == 0
        assert stats["ttl_seconds"] == 3600


class TestSystemPromptBuilder:
    """Test SystemPromptBuilder functionality."""

    def test_basic_initialization(self):
        """Test basic SystemPromptBuilder initialization."""
        builder = SystemPromptBuilder(cache_ttl=1800)

        # Check basic attributes
        assert builder.cache is not None
        assert builder.templates is not None
        assert len(builder.templates) > 0

    def test_default_templates_loaded(self):
        """Test that default templates are loaded."""
        builder = SystemPromptBuilder()

        # Should have default templates
        assert "minimal_context_ja" in builder.templates
        assert "contextual_document_assistant_ja" in builder.templates

    def test_generate_cache_key(self):
        """Test cache key generation."""
        builder = SystemPromptBuilder()

        repo_context = RepositoryContext(
            service=GitService.GITHUB, owner="test", repo="repo", ref="main"
        )

        doc_metadata = DocumentMetadata(title="Test Doc", type=DocumentType.MARKDOWN)

        cache_key = builder.generate_cache_key(
            repository_context=repo_context,
            document_metadata=doc_metadata,
            document_content="test content",
            template_id="test_template",
        )

        # Should be a non-empty string
        assert isinstance(cache_key, str)
        assert len(cache_key) > 0

    def test_sanitize_document_content(self):
        """Test document content sanitization."""
        builder = SystemPromptBuilder()

        # Test normal content
        normal_content = "This is normal content."
        sanitized = builder.sanitize_document_content(normal_content)
        assert sanitized == normal_content

        # Test long content
        long_content = "A" * 10000
        sanitized = builder.sanitize_document_content(long_content, max_length=1000)
        # Note: sanitized content may be slightly longer due to truncation message
        assert len(sanitized) <= 1050  # Allow some buffer for truncation message
        assert "..." in sanitized

    def test_build_system_prompt_basic(self):
        """Test basic system prompt building."""
        builder = SystemPromptBuilder()

        repo_context = RepositoryContext(
            service=GitService.GITHUB, owner="microsoft", repo="vscode", ref="main"
        )

        # Should build successfully with minimal context
        system_prompt = builder.build_system_prompt(
            template_id="minimal_context_ja", repository_context=repo_context
        )

        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0
        assert "microsoft/vscode" in system_prompt

    def test_build_system_prompt_with_document(self):
        """Test system prompt building with document context."""
        builder = SystemPromptBuilder()

        repo_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="microsoft",
            repo="vscode",
            ref="main",
            current_path="README.md",
        )

        doc_metadata = DocumentMetadata(
            title="Visual Studio Code", type=DocumentType.MARKDOWN, filename="README.md"
        )

        doc_content = "# Visual Studio Code\nA powerful code editor."

        system_prompt = builder.build_system_prompt(
            template_id="contextual_document_assistant_ja",
            repository_context=repo_context,
            document_metadata=doc_metadata,
            document_content=doc_content,
        )

        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0
        assert "microsoft/vscode" in system_prompt
        assert "README.md" in system_prompt

    def test_cache_functionality(self):
        """Test system prompt caching."""
        builder = SystemPromptBuilder()

        repo_context = RepositoryContext(
            service=GitService.GITHUB, owner="test", repo="repo", ref="main"
        )

        # First call - should generate and cache
        prompt1 = builder.build_system_prompt(
            template_id="minimal_context_ja", repository_context=repo_context
        )

        # Second call - should use cache
        prompt2 = builder.build_system_prompt(
            template_id="minimal_context_ja", repository_context=repo_context
        )

        # Should be identical
        assert prompt1 == prompt2

    def test_clear_cache(self):
        """Test cache clearing."""
        builder = SystemPromptBuilder()

        # Clear the cache
        builder.clear_cache()

        # Cache should be empty
        stats = builder.get_cache_stats()
        assert stats["total_items"] == 0

    def test_get_cache_stats(self):
        """Test cache statistics retrieval."""
        builder = SystemPromptBuilder()

        stats = builder.get_cache_stats()

        assert "total_items" in stats
        assert "valid_items" in stats
        assert "expired_items" in stats
        assert "ttl_seconds" in stats


class TestJapaneseSystemPromptBuilder:
    """Test JapaneseSystemPromptBuilder functionality."""

    def test_initialization(self):
        """Test JapaneseSystemPromptBuilder initialization."""
        japanese_builder = JapaneseSystemPromptBuilder()

        # Should have templates loaded
        assert japanese_builder.templates is not None
        assert len(japanese_builder.templates) > 0

    def test_template_selection(self):
        """Test template selection functionality."""
        japanese_builder = JapaneseSystemPromptBuilder()

        repo_context = RepositoryContext(
            service=GitService.GITHUB, owner="test", repo="repo", ref="main"
        )

        doc_metadata = DocumentMetadata(
            title="API Documentation", type=DocumentType.MARKDOWN
        )

        # Test template selection
        template_name = japanese_builder.select_appropriate_template(
            repository_context=repo_context, document_metadata=doc_metadata
        )

        assert isinstance(template_name, str)
        assert template_name in japanese_builder.templates

    def test_build_system_prompt_with_context(self):
        """Test building system prompt with full context."""
        japanese_builder = JapaneseSystemPromptBuilder()

        repo_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="microsoft",
            repo="vscode",
            ref="main",
            current_path="docs/api.md",
        )

        doc_metadata = DocumentMetadata(
            title="API Documentation", type=DocumentType.MARKDOWN, filename="api.md"
        )

        doc_content = "# API Documentation\nThis is the API guide."

        system_prompt = japanese_builder.build_system_prompt(
            repository_context=repo_context,
            document_metadata=doc_metadata,
            document_content=doc_content,
        )

        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0
        assert "microsoft/vscode" in system_prompt

    def test_build_system_prompt_minimal(self):
        """Test building system prompt with minimal context."""
        japanese_builder = JapaneseSystemPromptBuilder()

        repo_context = RepositoryContext(
            service=GitService.GITHUB, owner="test", repo="minimal", ref="main"
        )

        system_prompt = japanese_builder.build_system_prompt(
            repository_context=repo_context
        )

        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0
        assert "test/minimal" in system_prompt


class TestSystemPromptBuilderIntegration:
    """Integration tests for SystemPromptBuilder."""

    def test_multiple_builders_isolation(self):
        """Test that multiple builders are isolated."""
        builder1 = SystemPromptBuilder(cache_ttl=1800)
        builder2 = JapaneseSystemPromptBuilder(cache_ttl=3600)

        # Clear both caches
        builder1.clear_cache()
        builder2.clear_cache()

        # Use both builders
        repo_context = RepositoryContext(
            service=GitService.GITHUB, owner="test", repo="isolation", ref="main"
        )

        prompt1 = builder1.build_system_prompt(
            template_id="minimal_context_ja", repository_context=repo_context
        )

        prompt2 = builder2.build_system_prompt(repository_context=repo_context)

        # Both should work independently
        assert isinstance(prompt1, str)
        assert isinstance(prompt2, str)

    def test_different_contexts_different_prompts(self):
        """Test that different contexts produce different prompts."""
        builder = JapaneseSystemPromptBuilder()

        repo_context1 = RepositoryContext(
            service=GitService.GITHUB, owner="user1", repo="repo1", ref="main"
        )

        repo_context2 = RepositoryContext(
            service=GitService.GITLAB, owner="user2", repo="repo2", ref="develop"
        )

        prompt1 = builder.build_system_prompt(repository_context=repo_context1)
        prompt2 = builder.build_system_prompt(repository_context=repo_context2)

        # Should be different
        assert prompt1 != prompt2
        assert "user1/repo1" in prompt1
        assert "user2/repo2" in prompt2

    def test_caching_across_identical_requests(self):
        """Test caching works across identical requests."""
        builder = JapaneseSystemPromptBuilder()

        repo_context = RepositoryContext(
            service=GitService.GITHUB, owner="cache", repo="test", ref="main"
        )

        doc_metadata = DocumentMetadata(title="Cache Test", type=DocumentType.MARKDOWN)

        # Make multiple identical requests
        prompt1 = builder.build_system_prompt(
            repository_context=repo_context,
            document_metadata=doc_metadata,
            document_content="cache test content",
        )

        prompt2 = builder.build_system_prompt(
            repository_context=repo_context,
            document_metadata=doc_metadata,
            document_content="cache test content",
        )

        prompt3 = builder.build_system_prompt(
            repository_context=repo_context,
            document_metadata=doc_metadata,
            document_content="cache test content",
        )

        # All should be identical (from cache)
        assert prompt1 == prompt2 == prompt3

    def test_template_fallback_behavior(self):
        """Test template fallback behavior."""
        builder = JapaneseSystemPromptBuilder()

        repo_context = RepositoryContext(
            service=GitService.GITHUB, owner="fallback", repo="test", ref="main"
        )

        # Request non-existent template
        system_prompt = builder.build_system_prompt(
            template_id="non_existent_template", repository_context=repo_context
        )

        # Should fallback to default and still work
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0
        assert "fallback/test" in system_prompt
