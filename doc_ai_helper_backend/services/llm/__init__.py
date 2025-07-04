"""
LLM service package.

This package provides LLM service implementations and utilities.
"""

from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.services.llm.factory import LLMServiceFactory
from doc_ai_helper_backend.services.llm.mock_service import MockLLMService
from doc_ai_helper_backend.services.llm.openai_service import OpenAIService
from doc_ai_helper_backend.services.llm.template_manager import PromptTemplateManager
from doc_ai_helper_backend.services.llm.cache_service import LLMCacheService

# Deprecated - use doc_ai_helper_backend.services.mcp instead
from doc_ai_helper_backend.services.llm.mcp_adapter import MCPAdapter

# New MCP integration
from doc_ai_helper_backend.services.mcp import get_mcp_server, get_available_tools

# Register available LLM services
LLMServiceFactory.register("mock", MockLLMService)
LLMServiceFactory.register("openai", OpenAIService)

__all__ = [
    "LLMServiceBase",
    "LLMServiceFactory",
    "MockLLMService",
    "OpenAIService",
    "PromptTemplateManager",
    "LLMCacheService",
    "MCPAdapter",  # Deprecated
    # New MCP integration
    "get_mcp_server",
    "get_available_tools",
]
