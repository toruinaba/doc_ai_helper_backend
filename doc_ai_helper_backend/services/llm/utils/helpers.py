"""
General helper utilities for LLM services.

This module contains miscellaneous helper functions that don't fit
into specific functional categories.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Default token limits
DEFAULT_MAX_TOKENS = 8000


def get_current_timestamp() -> str:
    """
    Get the current timestamp as an ISO formatted string.

    Returns:
        str: Current timestamp in ISO format
    """
    return datetime.now().isoformat()


def safe_get_nested_value(
    data: Dict[str, Any], keys: List[str], default: Any = None
) -> Any:
    """
    Safely get a nested value from a dictionary.

    Args:
        data: The dictionary to search
        keys: List of keys representing the path to the value
        default: Default value to return if path not found

    Returns:
        Any: The value at the specified path or default
    """
    try:
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return default
        return data
    except (KeyError, TypeError, AttributeError):
        return default


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length, adding a suffix if truncated.

    Args:
        text: Text to truncate
        max_length: Maximum length of the result
        suffix: Suffix to add if text is truncated

    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text

    if len(suffix) >= max_length:
        return suffix[:max_length]

    return text[: max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing or replacing invalid characters.

    Args:
        filename: Original filename

    Returns:
        str: Sanitized filename
    """
    import re

    # Replace invalid characters with underscores
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)

    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(" .")

    # Ensure it's not empty
    if not sanitized:
        sanitized = "untitled"

    return sanitized


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)

    Returns:
        Dict[str, Any]: Merged dictionary
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


class SystemPromptCache:
    """Simple cache for system prompts with TTL."""

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Any] = {}
        self.cache_times: Dict[str, float] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache if it hasn't expired."""
        import time

        if key in self.cache:
            if time.time() - self.cache_times[key] < self.ttl_seconds:
                return self.cache[key]
            else:
                # Remove expired entry
                del self.cache[key]
                del self.cache_times[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set a value in cache with current timestamp."""
        import time

        self.cache[key] = value
        self.cache_times[key] = time.time()

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.cache_times.clear()


class SystemPromptBuilder:
    """Builder for system prompts with context awareness."""

    def __init__(self, cache_ttl: int = 3600):
        self.cache = SystemPromptCache(cache_ttl)
        self.base_prompt = "You are a helpful AI assistant."

    def build_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build a system prompt with optional context."""
        if not context:
            return self.base_prompt

        cache_key = str(hash(str(sorted(context.items()))))
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        prompt_parts = [self.base_prompt]

        if "repository" in context:
            prompt_parts.append(f"Repository: {context['repository']}")

        if "document_type" in context:
            prompt_parts.append(f"Document type: {context['document_type']}")

        prompt = "\n\n".join(prompt_parts)
        self.cache.set(cache_key, prompt)
        return prompt


class JapaneseSystemPromptBuilder(SystemPromptBuilder):
    """Japanese-specific system prompt builder."""

    def __init__(self, cache_ttl: int = 3600):
        super().__init__(cache_ttl)
        self.base_prompt = (
            "あなたは親切なAIアシスタントです。日本語で丁寧に回答してください。"
        )

    def build_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build a Japanese system prompt with optional context."""
        if not context:
            return self.base_prompt

        cache_key = f"ja_{str(hash(str(sorted(context.items()))))}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        prompt_parts = [self.base_prompt]

        if "repository" in context:
            prompt_parts.append(f"リポジトリ: {context['repository']}")

        if "document_type" in context:
            prompt_parts.append(f"ドキュメントタイプ: {context['document_type']}")

        prompt = "\n\n".join(prompt_parts)
        self.cache.set(cache_key, prompt)
        return prompt
