# -*- coding: utf-8 -*-
"""
LLM service package (refactored version).

This package provides refactored LLM service implementations and utilities.

Key components:
- orchestrator: Unified query processing orchestrator
- factory: Service factory with orchestrator integration
- providers: Provider implementations (OpenAI, Mock)
- base: Common base class
"""

# Core architecture components
from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.services.llm.orchestrator import LLMOrchestrator
from doc_ai_helper_backend.services.llm.factory import LLMServiceFactory

# Provider implementations
from doc_ai_helper_backend.services.llm.providers.openai_service import OpenAIService
from doc_ai_helper_backend.services.llm.providers.mock_service import MockLLMService

# Backward compatibility aliases
QueryManager = LLMOrchestrator
QueryOrchestrator = LLMOrchestrator

# MCP integration
try:
    from doc_ai_helper_backend.services.mcp import mcp_server
except ImportError:
    mcp_server = None

__all__ = [
    # Core architecture
    "LLMServiceBase",
    "LLMOrchestrator", 
    "LLMServiceFactory",
    # Providers
    "OpenAIService",
    "MockLLMService",
    # Backward compatibility
    "QueryManager",
    "QueryOrchestrator",
    # MCP integration
    "mcp_server",
]
