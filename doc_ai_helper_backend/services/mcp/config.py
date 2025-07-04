"""
MCP (Model Context Protocol) configuration.

This module provides configuration settings for the FastMCP server.
"""

import os
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


def create_mcp_config_from_env() -> MCPConfig:
    """
    Create MCP configuration from environment variables.

    Returns:
        MCPConfig instance with environment-based configuration
    """
    config = MCPConfig()

    # Git service configuration
    if os.getenv("FORGEJO_BASE_URL"):
        config.forgejo_base_url = os.getenv("FORGEJO_BASE_URL")
    if os.getenv("FORGEJO_TOKEN"):
        config.forgejo_token = os.getenv("FORGEJO_TOKEN")
    if os.getenv("FORGEJO_USERNAME"):
        config.forgejo_username = os.getenv("FORGEJO_USERNAME")
    if os.getenv("FORGEJO_PASSWORD"):
        config.forgejo_password = os.getenv("FORGEJO_PASSWORD")

    # Set default service based on available configuration
    if config.forgejo_base_url and (
        config.forgejo_token or (config.forgejo_username and config.forgejo_password)
    ):
        config.default_git_service = "forgejo"

    if os.getenv("GITHUB_TOKEN"):
        config.github_token = os.getenv("GITHUB_TOKEN")
        if (
            not config.forgejo_base_url
        ):  # Only set GitHub as default if Forgejo is not configured
            config.default_git_service = "github"

    return config


# Default configuration instance
default_mcp_config = create_mcp_config_from_env()
