"""
Tests for mock service constants.

This module tests the constants and configuration values used by the MockLLMService.
"""

import pytest
from doc_ai_helper_backend.services.llm.mock.constants import (
    RESPONSE_PATTERNS,
    ERROR_KEYWORDS,
    GITHUB_KEYWORDS,
    UTILITY_KEYWORDS,
    ANALYSIS_KEYWORDS,
    PREVIOUS_QUESTION_KEYWORDS,
    PREVIOUS_ANSWER_KEYWORDS,
    CONVERSATION_CONTINUATION_KEYWORDS,
    MOCK_TEMPLATE_NAMES,
    DEFAULT_MODELS,
    DEFAULT_CHUNK_SIZE,
    CHARACTERS_PER_TOKEN,
)


class TestMockConstants:
    """Test the mock service constants."""

    def test_response_patterns_exist(self):
        """Test that response patterns are defined and non-empty."""
        assert isinstance(RESPONSE_PATTERNS, dict)
        assert len(RESPONSE_PATTERNS) > 0
        assert "hello" in RESPONSE_PATTERNS
        assert "help" in RESPONSE_PATTERNS

    def test_keyword_lists_are_non_empty(self):
        """Test that all keyword lists are defined and non-empty."""
        keyword_lists = [
            ERROR_KEYWORDS,
            GITHUB_KEYWORDS,
            UTILITY_KEYWORDS,
            ANALYSIS_KEYWORDS,
            PREVIOUS_QUESTION_KEYWORDS,
            PREVIOUS_ANSWER_KEYWORDS,
            CONVERSATION_CONTINUATION_KEYWORDS,
        ]

        for keyword_list in keyword_lists:
            assert isinstance(keyword_list, list)
            assert len(keyword_list) > 0

    def test_default_models_configuration(self):
        """Test that default models are properly configured."""
        assert isinstance(DEFAULT_MODELS, dict)
        assert len(DEFAULT_MODELS) > 0

        # Check that each model has proper configuration
        for model_name, config in DEFAULT_MODELS.items():
            assert isinstance(model_name, str)
            assert isinstance(config, dict)
            assert "max_tokens" in config
            assert isinstance(config["max_tokens"], int)
            assert config["max_tokens"] > 0

    def test_mock_template_names(self):
        """Test that mock template names are defined."""
        assert isinstance(MOCK_TEMPLATE_NAMES, list)
        assert len(MOCK_TEMPLATE_NAMES) > 0
        assert all(isinstance(name, str) for name in MOCK_TEMPLATE_NAMES)

    def test_default_configuration_values(self):
        """Test that default configuration values are reasonable."""
        assert isinstance(DEFAULT_CHUNK_SIZE, int)
        assert DEFAULT_CHUNK_SIZE > 0

        assert isinstance(CHARACTERS_PER_TOKEN, int)
        assert CHARACTERS_PER_TOKEN > 0

    def test_specific_keyword_content(self):
        """Test that specific expected keywords are present."""
        # Error keywords
        assert "simulate_error" in ERROR_KEYWORDS
        assert "test_error" in ERROR_KEYWORDS

        # GitHub keywords
        assert "create issue" in GITHUB_KEYWORDS
        assert "create pr" in GITHUB_KEYWORDS

        # Utility keywords
        assert "current time" in UTILITY_KEYWORDS
        assert "calculate" in UTILITY_KEYWORDS

        # Analysis keywords
        assert "analyze" in ANALYSIS_KEYWORDS
        assert "examine" in ANALYSIS_KEYWORDS

    def test_conversation_keywords(self):
        """Test conversation-related keywords."""
        assert "前の質問" in PREVIOUS_QUESTION_KEYWORDS
        assert "previous question" in PREVIOUS_QUESTION_KEYWORDS

        assert "前の回答" in PREVIOUS_ANSWER_KEYWORDS
        assert "previous answer" in PREVIOUS_ANSWER_KEYWORDS

        assert "continue our conversation" in CONVERSATION_CONTINUATION_KEYWORDS
