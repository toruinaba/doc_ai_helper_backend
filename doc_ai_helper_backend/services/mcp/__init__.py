"""
MCP (Model Context Protocol) package for Document AI Helper.

This package provides FastMCP-based tools and services for document analysis,
feedback generation, and improvement suggestions.
"""

from .server import mcp_server, DocumentAIHelperMCPServer
from .config import MCPConfig, default_mcp_config


def get_mcp_server() -> DocumentAIHelperMCPServer:
    """
    Get the default MCP server instance.

    Returns:
        DocumentAIHelperMCPServer: The MCP server instance
    """
    return mcp_server


def get_available_tools() -> list:
    """
    Get list of available MCP tools.

    Returns:
        List of available tool names
    """
    return mcp_server.get_available_tools()


def list_tools_detailed() -> list:
    """
    Get detailed list of available MCP tools.

    Returns:
        List of tool dictionaries with name, description, and enabled status
    """
    return mcp_server.list_tools()


async def call_tool(tool_name: str, **kwargs):
    """
    Call a specific MCP tool.

    Args:
        tool_name: Name of the tool to call
        **kwargs: Arguments to pass to the tool

    Returns:
        Result of the tool execution
    """
    return await mcp_server.call_tool(tool_name, **kwargs)


__all__ = [
    "mcp_server",
    "DocumentAIHelperMCPServer",
    "MCPConfig",
    "default_mcp_config",
    "get_mcp_server",
    "get_available_tools",
    "list_tools_detailed",
    "call_tool",
]
