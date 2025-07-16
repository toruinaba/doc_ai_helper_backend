"""
MCP (Model Context Protocol) package for Document AI Helper.

This package provides FastMCP-based tools and services for document analysis,
feedback generation, and improvement suggestions.
"""

from .server import mcp_server, DocumentAIHelperMCPServer
from .config import MCPConfig, default_mcp_config

__all__ = [
    "mcp_server",
    "DocumentAIHelperMCPServer", 
    "MCPConfig",
    "default_mcp_config",
]
