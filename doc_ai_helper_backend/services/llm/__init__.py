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

# New refactored OpenAI components
from doc_ai_helper_backend.services.llm.openai_client import OpenAIAPIClient
from doc_ai_helper_backend.services.llm.openai_options_builder import (
    OpenAIOptionsBuilder,
)
from doc_ai_helper_backend.services.llm.openai_response_converter import (
    OpenAIResponseConverter,
)
from doc_ai_helper_backend.services.llm.openai_function_handler import (
    OpenAIFunctionHandler,
)

# MCP integration
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
    # New refactored OpenAI components
    "OpenAIAPIClient",
    "OpenAIOptionsBuilder",
    "OpenAIResponseConverter",
    "OpenAIFunctionHandler",
    # MCP integration
    "get_mcp_server",
    "get_available_tools",
]
