"""
LLM service package.

This package provides LLM service implementations and utilities.
"""

from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.services.llm.factory import LLMServiceFactory
from doc_ai_helper_backend.services.llm.mock_service import MockLLMService
from doc_ai_helper_backend.services.llm.template_manager import PromptTemplateManager
from doc_ai_helper_backend.services.llm.cache_service import LLMCacheService
from doc_ai_helper_backend.services.llm.mcp_adapter import MCPAdapter

# Register available LLM services
LLMServiceFactory.register("mock", MockLLMService)

__all__ = [
    "LLMServiceBase",
    "LLMServiceFactory",
    "MockLLMService",
    "PromptTemplateManager",
    "LLMCacheService",
    "MCPAdapter",
]
