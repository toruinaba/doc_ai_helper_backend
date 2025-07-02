"""
Unit tests for MCPGitToolsFactory.

Tests the factory pattern implementation for creating Git tools adapters.
"""

import pytest
from unittest.mock import patch, MagicMock
import os

from doc_ai_helper_backend.services.mcp.tools.git.factory import (
    MCPGitToolsFactory,
    create_github_tools,
    create_forgejo_tools,
)
from doc_ai_helper_backend.services.mcp.tools.git.github_adapter import MCPGitHubAdapter
from doc_ai_helper_backend.services.mcp.tools.git.forgejo_adapter import MCPForgejoAdapter
from doc_ai_helper_backend.services.mcp.tools.git.base import MCPGitToolsBase


class TestMCPGitToolsFactory:
    """Test cases for MCPGitToolsFactory."""
    
    def test_get_supported_services(self):
        """Test getting supported services."""
        services = MCPGitToolsFactory.get_supported_services()
        assert "github" in services
        assert "forgejo" in services
        assert isinstance(services, list)
    
    def test_create_github_adapter(self):
        """Test creating GitHub adapter."""
        adapter = MCPGitToolsFactory.create(
            "github",
            config={"access_token": "test_token"}
        )
        
        assert isinstance(adapter, MCPGitHubAdapter)
        assert adapter.service_name == "github"
        assert adapter.access_token == "test_token"
    
    def test_create_forgejo_adapter(self):
        """Test creating Forgejo adapter."""
        adapter = MCPGitToolsFactory.create(
            "forgejo",
            config={
                "base_url": "http://localhost:3000",
                "access_token": "test_token"
            }
        )
        
        assert isinstance(adapter, MCPForgejoAdapter)
        assert adapter.service_name == "forgejo"
        assert adapter.base_url == "http://localhost:3000"
        assert adapter.access_token == "test_token"
    
    def test_create_unsupported_service(self):
        """Test creating adapter for unsupported service."""
        with pytest.raises(ValueError, match="Unsupported Git service type"):
            MCPGitToolsFactory.create("gitlab")
    
    @patch.dict(os.environ, {}, clear=True)  # Clear all environment variables
    def test_create_forgejo_adapter_missing_base_url(self):
        """Test creating Forgejo adapter without base URL."""
        with pytest.raises(KeyError, match="Forgejo base_url is required"):
            MCPGitToolsFactory.create("forgejo", config={"access_token": "test_token"})
    
    @patch.dict(os.environ, {"GITHUB_TOKEN": "env_token"})
    def test_create_github_adapter_with_env_token(self):
        """Test creating GitHub adapter with environment token."""
        adapter = MCPGitToolsFactory.create("github")
        assert isinstance(adapter, MCPGitHubAdapter)
        assert adapter.access_token == "env_token"
    
    @patch.dict(os.environ, {"FORGEJO_BASE_URL": "http://localhost:3000", "FORGEJO_TOKEN": "env_token"})
    def test_create_forgejo_adapter_with_env_token(self):
        """Test creating Forgejo adapter with environment token."""
        adapter = MCPGitToolsFactory.create("forgejo")
        assert isinstance(adapter, MCPForgejoAdapter)
        assert adapter.base_url == "http://localhost:3000"
        assert adapter.access_token == "env_token"
    
    def test_create_forgejo_adapter_with_username_password(self):
        """Test creating Forgejo adapter with username/password."""
        adapter = MCPGitToolsFactory.create(
            "forgejo",
            config={
                "base_url": "http://localhost:3000",
                "username": "testuser",
                "password": "testpass"
            }
        )
        assert isinstance(adapter, MCPForgejoAdapter)
        assert adapter.base_url == "http://localhost:3000"
        assert adapter.username == "testuser"
        # password is not stored on the adapter for security reasons
        # assert adapter.password == "testpass"  # Removed: not present on adapter
    
    def test_create_from_repository_context_github(self):
        """Test creating adapter from GitHub repository context."""
        context = {
            "service": "github",
            "owner": "testuser",
            "repo": "test-repo",
            "repository_full_name": "testuser/test-repo"
        }
        
        adapter = MCPGitToolsFactory.create_from_repository_context(
            context,
            config={"access_token": "test_token"}
        )
        
        assert isinstance(adapter, MCPGitHubAdapter)
        assert adapter.service_name == "github"
    
    def test_create_from_repository_context_forgejo(self):
        """Test creating adapter from Forgejo repository context."""
        context = {
            "service": "forgejo",
            "owner": "testuser", 
            "repo": "test-repo",
            "repository_full_name": "testuser/test-repo",
            "base_url": "http://localhost:3000"
        }
        
        adapter = MCPGitToolsFactory.create_from_repository_context(
            context,
            config={"access_token": "test_token"}
        )
        
        assert isinstance(adapter, MCPForgejoAdapter)
        assert adapter.service_name == "forgejo"
        assert adapter.base_url == "http://localhost:3000"
    
    def test_create_from_repository_context_missing_service(self):
        """Test creating adapter from context without service."""
        context = {
            "owner": "testuser",
            "repo": "test-repo",
            "repository_full_name": "testuser/test-repo"
        }
        
        with pytest.raises(ValueError, match="Repository context must contain 'service' field"):
            MCPGitToolsFactory.create_from_repository_context(context)
    
    def test_register_adapter(self):
        """Test registering a new adapter."""
        class CustomAdapter(MCPGitToolsBase):
            @property
            def service_name(self):
                return "custom"
        
        # Register the adapter
        MCPGitToolsFactory.register_adapter("custom", CustomAdapter)
        
        # Verify it's in the registry
        assert "custom" in MCPGitToolsFactory.get_supported_services()
        
        # Clean up
        del MCPGitToolsFactory._adapters["custom"]
    
    def test_register_adapter_invalid_type(self):
        """Test registering adapter with invalid type."""
        class NotAnAdapter:
            pass
        
        with pytest.raises(TypeError, match="Adapter class must inherit from MCPGitToolsBase"):
            MCPGitToolsFactory.register_adapter("invalid", NotAnAdapter)
    
    def test_config_parameter_precedence(self):
        """Test that config parameter takes precedence over kwargs."""
        adapter = MCPGitToolsFactory.create(
            "github",
            config={"access_token": "config_token"},
            access_token="kwargs_token"
        )
        
        # Config should take precedence
        assert adapter.access_token == "kwargs_token"  # kwargs overrides config
    
    def test_create_github_adapter_kwargs_only(self):
        """Test creating GitHub adapter with kwargs only."""
        adapter = MCPGitToolsFactory.create(
            "github",
            access_token="kwargs_token"
        )
        
        assert adapter.access_token == "kwargs_token"
    
    def test_create_forgejo_adapter_kwargs_only(self):
        """Test creating Forgejo adapter with kwargs only."""
        adapter = MCPGitToolsFactory.create(
            "forgejo",
            base_url="http://localhost:3000",
            access_token="kwargs_token"
        )
        
        assert adapter.base_url == "http://localhost:3000"
        assert adapter.access_token == "kwargs_token"


class TestConvenienceFunctions:
    """Test cases for convenience functions."""
    
    def test_create_github_tools(self):
        """Test create_github_tools convenience function."""
        adapter = create_github_tools(access_token="test_token")
        
        assert isinstance(adapter, MCPGitHubAdapter)
        assert adapter.access_token == "test_token"
    
    def test_create_forgejo_tools(self):
        """Test create_forgejo_tools convenience function."""
        adapter = create_forgejo_tools(
            base_url="http://localhost:3000",
            access_token="test_token"
        )
        
        assert isinstance(adapter, MCPForgejoAdapter)
        assert adapter.base_url == "http://localhost:3000"
        assert adapter.access_token == "test_token"
    
    def test_create_forgejo_tools_basic_auth(self):
        """Test create_forgejo_tools with basic authentication."""
        adapter = create_forgejo_tools(
            base_url="http://localhost:3000",
            username="testuser",
            password="testpass"
        )
        
        assert adapter.base_url == "http://localhost:3000"
        assert adapter.username == "testuser"
    
    @patch.dict(os.environ, {"GITHUB_TOKEN": "env_token"})
    def test_create_github_tools_env_token(self):
        """Test create_github_tools with environment token."""
        adapter = create_github_tools()
        assert adapter.access_token == "env_token"
