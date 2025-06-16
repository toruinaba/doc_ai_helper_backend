"""
Cache service for LLM responses.

This module provides a simple in-memory cache for LLM responses.
"""

import time
import hashlib
import json
from typing import Dict, Any, Optional, Tuple

from doc_ai_helper_backend.models.llm import LLMResponse
from doc_ai_helper_backend.core.config import settings


class LLMCacheService:
    """
    Cache service for LLM responses.

    This service provides caching functionality for LLM responses to reduce
    API calls and improve performance.
    """

    def __init__(self, ttl_seconds: int = None):
        """
        Initialize the cache service.

        Args:
            ttl_seconds: Cache TTL in seconds (default: from settings)
        """
        self._cache: Dict[str, Tuple[LLMResponse, float]] = {}
        self.ttl_seconds = ttl_seconds or settings.llm_cache_ttl

    def generate_key(self, prompt: str, options: Dict[str, Any]) -> str:
        """
        Generate a cache key from prompt and options.

        Args:
            prompt: The prompt text
            options: The query options

        Returns:
            str: A hash key for the cache
        """
        # Create a deterministic representation of the input
        key_data = {
            "prompt": prompt,
            "options": {k: v for k, v in sorted(options.items()) if k != "stream"},
        }

        # Convert to JSON and hash
        serialized = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(serialized.encode()).hexdigest()

    def get(self, key: str) -> Optional[LLMResponse]:
        """
        Get an item from the cache.

        Args:
            key: The cache key

        Returns:
            Optional[LLMResponse]: The cached response or None if not found or expired
        """
        if key not in self._cache:
            return None

        response, expiry_time = self._cache[key]

        # Check if expired
        if time.time() > expiry_time:
            del self._cache[key]
            return None

        return response

    def set(self, key: str, response: LLMResponse) -> None:
        """
        Store an item in the cache.

        Args:
            key: The cache key
            response: The LLM response to cache
        """
        expiry_time = time.time() + self.ttl_seconds
        self._cache[key] = (response, expiry_time)

    def clear(self) -> None:
        """
        Clear all items from the cache.
        """
        self._cache.clear()

    def clear_expired(self) -> int:
        """
        Clear expired items from the cache.

        Returns:
            int: Number of items cleared
        """
        now = time.time()
        expired_keys = [
            key for key, (_, expiry_time) in self._cache.items() if now > expiry_time
        ]

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)
