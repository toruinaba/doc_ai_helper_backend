"""
Tests for the LLM cache utility functions.
"""

import pytest
import time
from unittest.mock import MagicMock

from doc_ai_helper_backend.models.llm import LLMResponse, LLMUsage
from doc_ai_helper_backend.services.llm.utils.caching import LLMCacheService


class TestLLMCacheService:
    """Tests for the LLMCacheService."""

    def test_generate_key(self):
        """Test generating cache keys."""
        cache_service = LLMCacheService(ttl_seconds=1)
        prompt = "Test prompt"
        options = {"model": "test-model", "temperature": 0.7}

        # Same prompt and options should generate the same key
        key1 = cache_service.generate_key(prompt, options)
        key2 = cache_service.generate_key(prompt, options)
        assert key1 == key2

        # Different prompt should generate different key
        key3 = cache_service.generate_key("Different prompt", options)
        assert key1 != key3

        # Different options should generate different key
        key4 = cache_service.generate_key(prompt, {"model": "other-model"})
        assert key1 != key4

        # Order of options shouldn't matter
        options_reordered = {"temperature": 0.7, "model": "test-model"}
        key5 = cache_service.generate_key(prompt, options_reordered)
        assert key1 == key5

        # Stream option should be ignored
        options_with_stream = {**options, "stream": True}
        key6 = cache_service.generate_key(prompt, options_with_stream)
        assert key1 == key6

    def test_get_set(self):
        """Test setting and getting items from cache."""
        cache_service = LLMCacheService(ttl_seconds=1)
        sample_response = LLMResponse(
            content="This is a test response",
            model="test-model",
            provider="test-provider",
            usage=LLMUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            raw_response={"id": "test-123"},
        )
        key = "test-key"

        # Initially should return None
        assert cache_service.get(key) is None

        # After setting, should return the response
        cache_service.set(key, sample_response)
        cached = cache_service.get(key)
        assert cached is not None
        assert cached.content == sample_response.content
        assert cached.model == sample_response.model

        # After expiry, should return None
        time.sleep(1.1)  # Wait for TTL to expire
        assert cache_service.get(key) is None

    def test_clear(self):
        """Test clearing the cache."""
        cache_service = LLMCacheService(ttl_seconds=10)
        sample_response = LLMResponse(
            content="This is a test response",
            model="test-model",
            provider="test-provider",
            usage=LLMUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            raw_response={"id": "test-123"},
        )
        key1 = "test-key-1"
        key2 = "test-key-2"

        cache_service.set(key1, sample_response)
        cache_service.set(key2, sample_response)

        assert cache_service.get(key1) is not None
        assert cache_service.get(key2) is not None

        cache_service.clear()

        assert cache_service.get(key1) is None
        assert cache_service.get(key2) is None

    def test_clear_expired(self):
        """Test clearing expired items."""
        cache_service = LLMCacheService(ttl_seconds=1)
        sample_response = LLMResponse(
            content="This is a test response",
            model="test-model",
            provider="test-provider",
            usage=LLMUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            raw_response={"id": "test-123"},
        )
        key1 = "test-key-1"
        key2 = "test-key-2"

        # Set two items
        cache_service.set(key1, sample_response)
        cache_service.set(key2, sample_response)

        # Wait for expiry
        time.sleep(1.1)  # Wait for TTL to expire

        # Clear expired items
        cleared = cache_service.clear_expired()

        # Should have cleared both items
        assert cleared == 2
        assert cache_service.get(key1) is None
        assert cache_service.get(key2) is None
