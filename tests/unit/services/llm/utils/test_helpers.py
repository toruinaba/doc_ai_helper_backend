"""
Tests for the helper utility functions.
"""

import pytest
import time
from unittest.mock import patch, MagicMock

from doc_ai_helper_backend.services.llm.messaging import (
    SystemPromptBuilder,
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
        cache = SystemPromptCache(ttl_hours=24)
        assert cache.ttl_seconds == 24 * 3600
        assert cache.cache_dir.exists()

    def test_cache_set_and_get(self):
        """Test setting and getting cached values."""
        cache = SystemPromptCache()

        # Create repository context
        repo_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test_owner",
            repo="test_repo",
            ref="main",
            current_path="test.md",
            base_url="https://github.com/test_owner/test_repo",
        )

        # Set a value
        cache.set(repo_context, "test_value")

        # Get the value
        result = cache.get(repo_context)
        assert result == "test_value"

    def test_cache_expiration(self):
        """Test cache expiration functionality."""
        # Use a very short TTL for testing
        cache = SystemPromptCache(ttl_hours=1 / 3600)  # 1 second

        # Create repository context
        repo_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test_owner",
            repo="test_repo",
            ref="main",
            current_path="test.md",
            base_url="https://github.com/test_owner/test_repo",
        )

        # Set a value
        cache.set(repo_context, "test_value")

        # Should be available immediately
        assert cache.get(repo_context) == "test_value"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired now
        assert cache.get(repo_context) is None

    def test_cache_miss(self):
        """Test cache miss behavior."""
        cache = SystemPromptCache()

        # Create repository context
        repo_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test_owner",
            repo="test_repo",
            ref="main",
            current_path="non_existent.md",
            base_url="https://github.com/test_owner/test_repo",
        )

        # Non-existent key should return None
        assert cache.get(repo_context) is None

    def test_cache_clear(self):
        """Test cache clearing."""
        cache = SystemPromptCache()

        # Create repository contexts
        repo_context1 = RepositoryContext(
            service=GitService.GITHUB,
            owner="test_owner",
            repo="test_repo",
            ref="main",
            current_path="test1.md",
            base_url="https://github.com/test_owner/test_repo",
        )
        repo_context2 = RepositoryContext(
            service=GitService.GITHUB,
            owner="test_owner",
            repo="test_repo",
            ref="main",
            current_path="test2.md",
            base_url="https://github.com/test_owner/test_repo",
        )

        # Add some items
        cache.set(repo_context1, "value1")
        cache.set(repo_context2, "value2")

        # Clear cache
        cache.clear()

        # Should be empty
        assert cache.get(repo_context1) is None
        assert cache.get(repo_context2) is None

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = SystemPromptCache(ttl_hours=1)

        # Create repository context
        repo_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test_owner",
            repo="test_repo",
            ref="main",
            current_path="test.md",
            base_url="https://github.com/test_owner/test_repo",
        )

        # Add some items
        cache.set(repo_context, "value1")

        stats = cache.get_stats()
        assert stats["total_files"] == 1


class TestSystemPromptBuilder:
    """Test SystemPromptBuilder functionality."""

    def test_basic_prompt_building(self):
        """Test basic system prompt building."""
        builder = SystemPromptBuilder()

        # Provide minimal required context to avoid template errors
        repo_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test_owner",
            repo="test_repo",
            ref="main",
            base_url="https://github.com/test_owner/test_repo",
        )

        doc_metadata = DocumentMetadata(
            filename="test.md",
            extension=".md",
            type=DocumentType.MARKDOWN,
            frontmatter={},
            title="Test Document",
            description="A test document",
            author="Test Author",
            date="2023-01-01",
            tags=["test", "example"],
        )

        prompt = builder.build_system_prompt(
            repository_context=repo_context, document_metadata=doc_metadata
        )
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_prompt_with_context(self):
        """Test system prompt building with repository context."""
        builder = SystemPromptBuilder()

        repo_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test_owner",
            repo="test_repo",
            ref="main",
            base_url="https://github.com/test_owner/test_repo",
        )

        prompt = builder.build_system_prompt(repository_context=repo_context)
        assert "test_owner" in prompt or "test_repo" in prompt

    def test_prompt_with_document_metadata(self):
        """Test system prompt building with document metadata."""
        builder = SystemPromptBuilder()

        # Also provide repository context to satisfy template requirements
        repo_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test_owner",
            repo="test_repo",
            ref="main",
            base_url="https://github.com/test_owner/test_repo",
        )

        doc_metadata = DocumentMetadata(
            filename="test.md",
            extension=".md",
            type=DocumentType.MARKDOWN,
            frontmatter={},
            title="Test Document",
            description="A test document",
            author="Test Author",
            date="2023-01-01",
            tags=["test", "example"],
        )

        prompt = builder.build_system_prompt(
            repository_context=repo_context, document_metadata=doc_metadata
        )
        # The prompt should include repository or document information
        assert "test_owner" in prompt or "test_repo" in prompt

    def test_prompt_caching(self):
        """Test system prompt caching."""
        builder = SystemPromptBuilder()

        # Provide minimal required context
        repo_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test_owner",
            repo="test_repo",
            ref="main",
            base_url="https://github.com/test_owner/test_repo",
        )

        doc_metadata = DocumentMetadata(
            filename="test.md",
            extension=".md",
            type=DocumentType.MARKDOWN,
            frontmatter={},
            title="Test Document",
            description="A test document",
            author="Test Author",
            date="2023-01-01",
            tags=["test", "example"],
        )

        # First call should build and cache
        prompt1 = builder.build_system_prompt(
            repository_context=repo_context, document_metadata=doc_metadata
        )

        # Second call should return cached result
        prompt2 = builder.build_system_prompt(
            repository_context=repo_context, document_metadata=doc_metadata
        )

        assert prompt1 == prompt2


class TestSystemPromptBuilderBasic:
    """Test basic SystemPromptBuilder functionality without document content."""

    def test_prompt_with_repository_context_only(self):
        """Test system prompt building with repository context only."""
        builder = SystemPromptBuilder()

        repo_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test_owner",
            repo="test_repo",
            ref="main",
            current_path="test.md",
            base_url="https://github.com/test_owner/test_repo",
        )

        prompt = builder.build_system_prompt(repository_context=repo_context)
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_prompt_with_metadata(self):
        """Test system prompt building with metadata."""
        builder = SystemPromptBuilder()

        repo_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test_owner",
            repo="test_repo",
            ref="main",
            current_path="test.md",
            base_url="https://github.com/test_owner/test_repo",
        )

        doc_metadata = DocumentMetadata(
            filename="test.md",
            extension=".md",
            type=DocumentType.MARKDOWN,
            frontmatter={},
            title="Test Document",
            description="A test document",
            author="Test Author",
            date="2023-01-01",
            tags=["test", "example"],
        )

        prompt = builder.build_system_prompt(
            repository_context=repo_context,
            document_metadata=doc_metadata,
        )
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_prompt_with_custom_instructions(self):
        """Test system prompt building with custom instructions."""
        builder = SystemPromptBuilder()

        repo_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test_owner",
            repo="test_repo",
            ref="main",
            current_path="test.md",
            base_url="https://github.com/test_owner/test_repo",
        )

        custom_instructions = "Please focus on documentation quality."

        prompt = builder.build_system_prompt(
            repository_context=repo_context,
            custom_instructions=custom_instructions,
        )
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "documentation quality" in prompt.lower()

    def test_prompt_cache_with_different_contexts(self):
        """Test that different contexts produce different cached prompts."""
        builder = SystemPromptBuilder()

        # Build prompt with first context
        repo_context1 = RepositoryContext(
            service=GitService.GITHUB,
            owner="owner1",
            repo="repo1",
            ref="main",
            current_path="file1.md",
            base_url="https://github.com/owner1/repo1",
        )

        # Build prompt with second context
        repo_context2 = RepositoryContext(
            service=GitService.GITHUB,
            owner="owner2",
            repo="repo2",
            ref="main",
            current_path="file2.md",
            base_url="https://github.com/owner2/repo2",
        )

        prompt1 = builder.build_system_prompt(repository_context=repo_context1)
        prompt2 = builder.build_system_prompt(repository_context=repo_context2)

        # Different contexts should produce different prompts
        assert prompt1 != prompt2


class TestHelperUtilities:
    """Test utility functions in helpers module."""

    def test_get_current_timestamp(self):
        """Test current timestamp utility."""
        from doc_ai_helper_backend.services.llm.utils.helpers import (
            get_current_timestamp,
        )

        timestamp = get_current_timestamp()
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0
        # Should be in ISO format
        assert "T" in timestamp

    def test_safe_get_nested_value_basic(self):
        """Test safe nested value retrieval - basic case."""
        from doc_ai_helper_backend.services.llm.utils.helpers import (
            safe_get_nested_value,
        )

        data = {"level1": {"level2": {"target": "found"}}}

        # Test successful retrieval
        result = safe_get_nested_value(data, ["level1", "level2", "target"])
        assert result == "found"

    def test_safe_get_nested_value_missing(self):
        """Test safe nested value retrieval - missing path."""
        from doc_ai_helper_backend.services.llm.utils.helpers import (
            safe_get_nested_value,
        )

        data = {"level1": {"level2": {"target": "found"}}}

        # Test missing path with default
        result = safe_get_nested_value(data, ["level1", "missing", "target"], "default")
        assert result == "default"

        # Test missing path without default
        result = safe_get_nested_value(data, ["missing", "path"], None)
        assert result is None

    def test_safe_get_nested_value_edge_cases(self):
        """Test safe nested value retrieval - edge cases."""
        from doc_ai_helper_backend.services.llm.utils.helpers import (
            safe_get_nested_value,
        )

        # Test with empty dict
        result = safe_get_nested_value({}, ["key"], "default")
        assert result == "default"

        # Test with None input
        result = safe_get_nested_value(None, ["key"], "default")
        assert result == "default"

        # Test with non-dict value in path
        data = {"level1": "not_a_dict"}
        result = safe_get_nested_value(data, ["level1", "nested"], "default")
        assert result == "default"


class TestSystemPromptBuilderEnhanced:
    """Additional tests for SystemPromptBuilder."""

    def test_builder_without_context(self):
        """Test SystemPromptBuilder without context."""
        from doc_ai_helper_backend.services.llm.utils.helpers import SystemPromptBuilder

        builder = SystemPromptBuilder()
        prompt = builder.build_prompt()

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert prompt == builder.base_prompt

    def test_builder_with_repository_context(self):
        """Test SystemPromptBuilder with repository context."""
        from doc_ai_helper_backend.services.llm.utils.helpers import SystemPromptBuilder

        builder = SystemPromptBuilder()
        context = {"repository": "test-repo", "document_type": "markdown"}

        prompt = builder.build_prompt(context)

        assert isinstance(prompt, str)
        assert "test-repo" in prompt
        assert "markdown" in prompt

    def test_builder_caching_mechanism(self):
        """Test SystemPromptBuilder caching."""
        from doc_ai_helper_backend.services.llm.utils.helpers import SystemPromptBuilder

        builder = SystemPromptBuilder()
        context = {"repository": "test-repo"}

        # First call
        prompt1 = builder.build_prompt(context)

        # Second call with same context (should use cache)
        prompt2 = builder.build_prompt(context)

        assert prompt1 == prompt2

    def test_builder_cache_key_generation(self):
        """Test SystemPromptBuilder cache key generation."""
        from doc_ai_helper_backend.services.llm.utils.helpers import SystemPromptBuilder

        builder = SystemPromptBuilder()

        # Different contexts should generate different cache keys
        context1 = {"repository": "repo1"}
        context2 = {"repository": "repo2"}

        prompt1 = builder.build_prompt(context1)
        prompt2 = builder.build_prompt(context2)

        assert prompt1 != prompt2


class TestSystemPromptCacheEnhanced:
    """Additional tests for SystemPromptCache."""

    def test_cache_ttl_initialization(self):
        """Test cache TTL initialization."""
        from doc_ai_helper_backend.services.llm.utils.helpers import SystemPromptCache

        # Test default TTL
        cache1 = SystemPromptCache()
        assert cache1.ttl_seconds == 3600  # Default 1 hour

        # Test custom TTL
        cache2 = SystemPromptCache(ttl_seconds=7200)
        assert cache2.ttl_seconds == 7200

    def test_cache_stats_with_expired_items(self):
        """Test cache stats with expired items."""
        from doc_ai_helper_backend.services.llm.utils.helpers import SystemPromptCache

        cache = SystemPromptCache(ttl_seconds=1)

        # Add items
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Wait for expiration
        time.sleep(1.1)

        # Add a new item
        cache.set("key3", "value3")

        stats = cache.get_stats()
        assert stats["total_items"] == 3
        assert stats["valid_items"] == 1  # Only key3 should be valid
        assert stats["expired_items"] == 2  # key1 and key2 should be expired

    def test_cache_cleanup_on_get(self):
        """Test that expired items are cleaned up on get."""
        from doc_ai_helper_backend.services.llm.utils.helpers import SystemPromptCache

        cache = SystemPromptCache(ttl_seconds=1)

        # Add an item
        cache.set("expiring_key", "value")

        # Verify it's there
        assert cache.get("expiring_key") == "value"

        # Wait for expiration
        time.sleep(1.1)

        # Try to get expired item
        result = cache.get("expiring_key")
        assert result is None

    def test_cache_multiple_operations(self):
        """Test multiple cache operations."""
        from doc_ai_helper_backend.services.llm.utils.helpers import SystemPromptCache

        cache = SystemPromptCache(ttl_seconds=3600)

        # Test setting multiple values
        values = {"key1": "value1", "key2": "value2", "key3": "value3"}
        for key, value in values.items():
            cache.set(key, value)

        # Test getting all values
        for key, expected_value in values.items():
            assert cache.get(key) == expected_value

        # Test clearing
        cache.clear()

        # All values should be gone
        for key in values.keys():
            assert cache.get(key) is None
