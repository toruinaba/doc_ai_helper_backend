"""
MCP (Model Context Protocol) configuration.

This module provides configuration settings for the FastMCP server.
"""

from typing import Optional, List, Dict, Any
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

    enable_github_tools: bool = Field(
        default=True, description="Enable GitHub integration tools"
    )

    enable_analysis_tools: bool = Field(
        default=True, description="Enable document analysis tools"
    )

    enable_utility_tools: bool = Field(
        default=True, description="Enable utility tools for testing and demonstration"
    )

    # Security settings
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["*"], description="Allowed origins for CORS"
    )

    max_content_length: int = Field(
        default=1024 * 1024, description="Maximum content length for processing"  # 1MB
    )

    max_tools_per_request: int = Field(
        default=10, description="Maximum number of tools that can be called per request"
    )

    # Git services integration settings
    default_git_service: str = Field(
        default="github", description="Default Git service for operations"
    )

    # GitHub integration settings
    github_token: Optional[str] = Field(
        default=None, description="GitHub API token for integration features"
    )

    github_default_labels: List[str] = Field(
        default_factory=lambda: ["documentation", "improvement"],
        description="Default labels for GitHub issues",
    )

    # Forgejo integration settings
    forgejo_base_url: Optional[str] = Field(
        default=None, description="Forgejo instance base URL"
    )

    forgejo_token: Optional[str] = Field(
        default=None, description="Forgejo API token for integration features"
    )

    forgejo_username: Optional[str] = Field(
        default=None, description="Forgejo username for basic authentication"
    )

    forgejo_password: Optional[str] = Field(
        default=None, description="Forgejo password for basic authentication"
    )

    forgejo_default_labels: List[str] = Field(
        default_factory=lambda: ["documentation", "improvement"],
        description="Default labels for Forgejo issues",
    )

    # Analysis settings
    default_analysis_model: str = Field(
        default="gpt-3.5-turbo", description="Default model for document analysis"
    )

    analysis_max_tokens: int = Field(
        default=4000, description="Maximum tokens for analysis operations"
    )


# Default configuration instance
default_mcp_config = MCPConfig()
