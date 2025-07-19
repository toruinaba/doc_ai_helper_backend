"""
MCP (Model Context Protocol) configuration.

This module provides configuration settings for the FastMCP server.
"""

import os
from typing import Optional, List
from pydantic import BaseModel, Field


class MCPConfig(BaseModel):
    """Configuration for MCP server."""

    server_name: str = Field(
        default="doc-ai-helper", description="Name of the MCP server"
    )

    server_version: str = Field(
        default="1.0.0", description="Version of the MCP server"
    )

    description: str = Field(
        default="Document AI Helper MCP Server for document analysis and feedback generation",
        description="Server description",
    )

    # Tool configuration
    enable_document_tools: bool = Field(
        default=True, description="Enable document processing tools"
    )

    enable_feedback_tools: bool = Field(
        default=True, description="Enable feedback generation tools"
    )

    enable_analysis_tools: bool = Field(
        default=True, description="Enable document analysis tools"
    )

    # Security settings
    max_content_length: int = Field(
        default=1024 * 1024, description="Maximum content length for processing"  # 1MB
    )

    max_tools_per_request: int = Field(
        default=10, description="Maximum number of tools that can be called per request"
    )


def create_mcp_config_from_env() -> MCPConfig:
    """
    Create MCP configuration from environment variables.

    Returns:
        MCPConfig instance with environment-based configuration
    """
    return MCPConfig(
        server_name=os.getenv("MCP_SERVER_NAME", "doc-ai-helper"),
        server_version=os.getenv("MCP_SERVER_VERSION", "1.0.0"),
        description=os.getenv(
            "MCP_SERVER_DESCRIPTION", 
            "Document AI Helper MCP Server for document analysis and feedback generation"
        ),
        enable_document_tools=os.getenv("MCP_ENABLE_DOCUMENT_TOOLS", "true").lower() == "true",
        enable_feedback_tools=os.getenv("MCP_ENABLE_FEEDBACK_TOOLS", "true").lower() == "true",
        enable_analysis_tools=os.getenv("MCP_ENABLE_ANALYSIS_TOOLS", "true").lower() == "true",
        max_content_length=int(os.getenv("MCP_MAX_CONTENT_LENGTH", "1048576")),  # 1MB
        max_tools_per_request=int(os.getenv("MCP_MAX_TOOLS_PER_REQUEST", "10")),
    )


# Default configuration instance
default_mcp_config = create_mcp_config_from_env()
