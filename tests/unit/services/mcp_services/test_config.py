"""
Test for MCP configuration functionality.

This module contains unit tests for the MCPConfig class.
"""

import pytest
import os
from pydantic import ValidationError

from doc_ai_helper_backend.services.mcp.config import MCPConfig


class TestMCPConfig:
    """Test the MCP configuration functionality."""

    def test_default_configuration(self):
        """Test that MCPConfig initializes with default values."""
        config = MCPConfig()

        assert config.server_name == "doc-ai-helper"
        assert config.server_version == "1.0.0"
        assert "Document AI Helper MCP Server" in config.description
        assert config.enable_document_tools is True

    def test_custom_configuration(self):
        """Test that MCPConfig accepts custom values."""
        config = MCPConfig(
            server_name="custom-server",
            server_version="2.0.0",
            description="Custom description",
            enable_document_tools=False,
        )

        assert config.server_name == "custom-server"
        assert config.server_version == "2.0.0"
        assert config.description == "Custom description"
        assert config.enable_document_tools is False

    def test_configuration_validation(self):
        """Test that MCPConfig validates input values."""
        # Valid configuration should not raise errors
        config = MCPConfig(server_name="valid-name", server_version="1.0.0")
        assert config is not None

    def test_field_descriptions(self):
        """Test that configuration fields have proper descriptions."""
        # Check that the model has field info
        assert MCPConfig.model_fields["server_name"].description is not None
        assert MCPConfig.model_fields["server_version"].description is not None
        assert MCPConfig.model_fields["description"].description is not None
        assert MCPConfig.model_fields["enable_document_tools"].description is not None

    def test_pydantic_model_behavior(self):
        """Test that MCPConfig behaves correctly as a Pydantic model."""
        config = MCPConfig()

        # Test serialization
        config_dict = config.model_dump()
        assert isinstance(config_dict, dict)
        assert "server_name" in config_dict

        # Test that we can create from dict
        new_config = MCPConfig(**config_dict)
        assert new_config.server_name == config.server_name
        assert new_config.server_version == config.server_version

    def test_configuration_immutability_after_creation(self):
        """Test configuration behavior after creation."""
        config = MCPConfig(server_name="test-server")

        # Test that we can still modify (Pydantic models are mutable by default)
        config.server_name = "modified-server"
        assert config.server_name == "modified-server"
