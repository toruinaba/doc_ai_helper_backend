"""
Test for LLM service common functionality.

This module contains unit tests for the LLMServiceCommon class.
Note: LLMServiceCommon is a composition helper class used by actual LLM services.
"""

import pytest

from doc_ai_helper_backend.services.llm.common import LLMServiceCommon


class TestLLMServiceCommon:
    """Test the LLM service common functionality."""

    @pytest.fixture
    def common_service(self):
        return LLMServiceCommon()

    def test_initialization(self, common_service):
        """Test that LLMServiceCommon initializes correctly."""
        assert common_service is not None
        assert hasattr(common_service, "template_manager")
        assert hasattr(common_service, "cache_service")
        assert hasattr(common_service, "system_prompt_builder")
        assert hasattr(common_service, "function_manager")

    def test_cache_key_generation(self, common_service):
        """Test cache key generation functionality."""
        # Test that cache key generation method exists and can be called
        assert hasattr(common_service, "_generate_cache_key")

        # Test basic cache key generation
        key = common_service._generate_cache_key(
            prompt="test prompt",
            conversation_history=None,
            options=None,
            repository_context=None,
            document_metadata=None,
            document_content=None,
            system_prompt_template="default",
        )
        assert isinstance(key, str)
        assert len(key) > 0

    def test_common_service_composition(self, common_service):
        """Test that common service has expected composition components."""
        # Verify template manager
        from doc_ai_helper_backend.services.llm.utils.templating import (
            PromptTemplateManager,
        )

        assert isinstance(common_service.template_manager, PromptTemplateManager)

        # Verify cache service
        from doc_ai_helper_backend.services.llm.utils.caching import LLMCacheService

        assert isinstance(common_service.cache_service, LLMCacheService)

        # Verify system prompt builder
        from doc_ai_helper_backend.services.llm.utils.helpers import (
            JapaneseSystemPromptBuilder,
        )

        assert isinstance(
            common_service.system_prompt_builder, JapaneseSystemPromptBuilder
        )

        # Verify function manager
        from doc_ai_helper_backend.services.llm.utils.functions import (
            FunctionCallManager,
        )

        assert isinstance(common_service.function_manager, FunctionCallManager)
