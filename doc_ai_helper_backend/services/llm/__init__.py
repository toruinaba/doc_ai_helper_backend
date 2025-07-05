"""
LLM service package.

This package provides LLM service implementations and utilities.
"""

# New composition-based architecture (now main implementation)
from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.services.llm.common import LLMServiceCommon
from doc_ai_helper_backend.services.llm.openai_service import OpenAIService

# Legacy classes (for backward compatibility during transition)
# from doc_ai_helper_backend.services.llm.legacy.base_legacy import LLMServiceBase as LegacyLLMServiceBase
# from doc_ai_helper_backend.services.llm.legacy.openai_service_legacy import OpenAIService as LegacyOpenAIService

# Factory and utilities
from doc_ai_helper_backend.services.llm.factory import LLMServiceFactory
from doc_ai_helper_backend.services.llm.mock_service import MockLLMService
from doc_ai_helper_backend.services.llm.utils import PromptTemplateManager, LLMCacheService

# MCP integration
from doc_ai_helper_backend.services.mcp import get_mcp_server, get_available_tools

# Register available LLM services with new composition-based implementation
LLMServiceFactory.register("mock", MockLLMService)
LLMServiceFactory.register("openai", OpenAIService)

__all__ = [
    # New composition-based architecture
    "LLMServiceBase",
    "LLMServiceCommon",
    "OpenAIService",
    # Factory and utilities
    "LLMServiceFactory",
    "MockLLMService", 
    "PromptTemplateManager",
    "LLMCacheService",
    # MCP integration
    "get_mcp_server",
    "get_available_tools",
]
