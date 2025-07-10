"""
Tests for prompt manager utilities.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from doc_ai_helper_backend.services.llm.messaging.prompt_manager import (
    SystemPromptCache,
    SystemPromptBuilder,
)


# Helper classes for testing
class SimpleContext:
    """Simple context class that mimics the repository context interface"""

    def __init__(
        self, owner="test_owner", repo="test_repo", path="test_path", ref="main"
    ):
        self.owner = owner
        self.repo = repo
        self.current_path = path
        self.ref = ref

    def model_dump(self):
        return {
            "owner": self.owner,
            "repo": self.repo,
            "current_path": self.current_path,
            "ref": self.ref,
        }


class SimpleMetadata:
    """Simple metadata class that mimics the document metadata interface"""

    def __init__(self, filename="test.py", is_doc=False, is_code=True):
        self.filename = filename
        self.is_documentation = is_doc
        self.is_code_file = is_code

    def model_dump(self):
        return {
            "filename": self.filename,
            "is_documentation": self.is_documentation,
            "is_code_file": self.is_code_file,
        }


class TestSystemPromptCache:
    """Test the SystemPromptCache class."""

    def test_cache_initialization(self):
        """Test cache initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SystemPromptCache(cache_dir=temp_dir)
            assert hasattr(cache, "cache_dir")
            assert hasattr(cache, "ttl_seconds")
            assert cache.cache_dir == Path(temp_dir)

    def test_get_nonexistent_key(self):
        """Test getting a non-existent cache key."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SystemPromptCache(cache_dir=temp_dir)
            context = SimpleContext()
            result = cache.get(context)
            assert result is None

    def test_set_and_get_cache(self):
        """Test setting and getting cache values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SystemPromptCache(cache_dir=temp_dir)
            context = SimpleContext()
            value = "test_prompt_value"

            cache.set(context, value)
            result = cache.get(context)

            assert result == value

    def test_cache_expiry(self):
        """Test cache expiry functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SystemPromptCache(
                cache_dir=temp_dir, ttl_hours=0
            )  # 0 hour TTL for immediate expiry
            context = SimpleContext()
            value = "test_value"
            cache.set(context, value)

            # With 0 TTL, the cache should be expired immediately
            result = cache.get(context)
            assert result is None

    def test_clear_cache(self):
        """Test clearing the cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SystemPromptCache(cache_dir=temp_dir)

            context1 = SimpleContext("owner1", "repo1", "path1", "main")
            context2 = SimpleContext("owner2", "repo2", "path2", "main")

            cache.set(context1, "value1")
            cache.set(context2, "value2")

            cache.clear()

            assert cache.get(context1) is None
            assert cache.get(context2) is None


class TestSystemPromptBuilder:
    """Test the SystemPromptBuilder class."""

    def test_builder_initialization(self):
        """Test builder initialization."""
        builder = SystemPromptBuilder()
        assert hasattr(builder, "cache")

    def test_build_system_prompt(self):
        """Test building system prompt."""
        builder = SystemPromptBuilder()
        context = SimpleContext()
        prompt = builder.build_system_prompt(context)

        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_build_system_prompt_caching(self):
        """Test that system prompt building uses caching."""
        with tempfile.TemporaryDirectory() as temp_dir:
            builder = SystemPromptBuilder(cache_dir=temp_dir)
            context = SimpleContext()

            # First call
            prompt1 = builder.build_system_prompt(context)

            # Second call with same context
            prompt2 = builder.build_system_prompt(context)

            # Should return same result
            assert prompt1 == prompt2

    def test_build_system_prompt_with_document_metadata(self):
        """Test building system prompt with document metadata."""
        builder = SystemPromptBuilder()
        context = SimpleContext()
        metadata = SimpleMetadata()

        prompt = builder.build_system_prompt(context, metadata)

        assert isinstance(prompt, str)
        assert len(prompt) > 0
