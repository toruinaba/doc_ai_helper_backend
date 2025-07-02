"""
Integration tests for MCP Git tools with server.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from doc_ai_helper_backend.services.mcp.server import DocumentAIHelperMCPServer
from doc_ai_helper_backend.services.mcp.config import MCPConfig
from doc_ai_helper_backend.models.repository_context import RepositoryContext


class TestMCPServerGitToolsIntegration:
    """Integration tests for Git tools with MCP server."""

    def test_server_initialization_with_github_config(self):
        """Test server initialization with GitHub configuration."""
        config = MCPConfig(
            enable_github_tools=True,
            github_token="test_token",
            default_git_service="github",
            github_default_labels=["bug", "enhancement"],
        )
        
        with patch('doc_ai_helper_backend.services.mcp.tools.git_tools.configure_git_service') as mock_configure:
            server = DocumentAIHelperMCPServer(config)
            
            # Verify GitHub service was configured
            mock_configure.assert_called_with(
                "github",
                config={
                    "access_token": "test_token",
                    "default_labels": ["bug", "enhancement"],
                },
                set_as_default=True
            )

    def test_server_initialization_with_forgejo_config(self):
        """Test server initialization with Forgejo configuration."""
        config = MCPConfig(
            enable_github_tools=True,  # This enables Git tools in general
            forgejo_base_url="https://forgejo.example.com",
            forgejo_token="forgejo_token",
            default_git_service="forgejo",
            forgejo_default_labels=["feature"],
        )
        
        with patch('doc_ai_helper_backend.services.mcp.tools.git_tools.configure_git_service') as mock_configure:
            server = DocumentAIHelperMCPServer(config)
            
            # Verify Forgejo service was configured
            mock_configure.assert_called_with(
                "forgejo",
                config={
                    "base_url": "https://forgejo.example.com",
                    "access_token": "forgejo_token",
                    "username": None,
                    "password": None,
                    "default_labels": ["feature"],
                },
                set_as_default=True
            )

    def test_server_initialization_with_both_services(self):
        """Test server initialization with both GitHub and Forgejo configured."""
        config = MCPConfig(
            enable_github_tools=True,
            github_token="github_token",
            forgejo_base_url="https://forgejo.example.com",
            forgejo_username="testuser",
            forgejo_password="testpass",
            default_git_service="github",
        )
        
        with patch('doc_ai_helper_backend.services.mcp.tools.git_tools.configure_git_service') as mock_configure:
            server = DocumentAIHelperMCPServer(config)
            
            # Verify both services were configured
            assert mock_configure.call_count == 2
            
            # Check GitHub configuration
            github_call = None
            forgejo_call = None
            for call in mock_configure.call_args_list:
                if call[0][0] == "github":
                    github_call = call
                elif call[0][0] == "forgejo":
                    forgejo_call = call
            
            assert github_call is not None
            assert forgejo_call is not None
            
            # Verify GitHub is set as default
            assert github_call[1]["set_as_default"] is True
            assert forgejo_call[1]["set_as_default"] is False

    def test_server_initialization_without_git_tools_disabled(self):
        """Test server initialization with Git tools disabled."""
        config = MCPConfig(
            enable_github_tools=False,
            github_token="test_token",
        )
        
        with patch('doc_ai_helper_backend.services.mcp.tools.git_tools.configure_git_service') as mock_configure:
            server = DocumentAIHelperMCPServer(config)
            
            # Verify no Git services were configured
            mock_configure.assert_not_called()

    @pytest.mark.asyncio
    async def test_server_git_tools_registration(self):
        """Test that Git tools are properly registered with FastMCP."""
        config = MCPConfig(
            enable_github_tools=True,
            github_token="test_token",
            default_git_service="github",
        )
        
        with patch('doc_ai_helper_backend.services.mcp.tools.git_tools.configure_git_service'):
            server = DocumentAIHelperMCPServer(config)
            
            # Check that the tools are registered in the FastMCP app
            registered_tools = server.app.get_tools()
            tool_names = [tool.name for tool in registered_tools]
            
            assert "create_git_issue" in tool_names
            assert "create_git_pull_request" in tool_names
            assert "check_git_repository_permissions" in tool_names

    @pytest.mark.asyncio
    async def test_server_tool_execution_create_issue(self):
        """Test executing create_git_issue tool through server."""
        config = MCPConfig(
            enable_github_tools=True,
            github_token="test_token",
            default_git_service="github",
        )
        
        with patch('doc_ai_helper_backend.services.mcp.tools.git_tools.configure_git_service'), \
             patch('doc_ai_helper_backend.services.mcp.tools.git_tools.create_git_issue') as mock_create_issue:
            
            mock_create_issue.return_value = "Issue created successfully: #123"
            
            server = DocumentAIHelperMCPServer(config)
            
            # Simulate repository context
            repo_context = RepositoryContext(
                owner="owner", repo="repo", service="github", ref="main", path=""
            )
            server._current_repository_context = repo_context
            
            # Execute the tool through FastMCP
            tools = server.app.get_tools()
            create_issue_tool = next(tool for tool in tools if tool.name == "create_git_issue")
            
            result = await create_issue_tool.handler(
                title="Test Issue",
                description="This is a test issue",
                labels=["bug"],
                assignees=["user1"],
                service_type="github",
                github_token="runtime_token",
            )
            
            assert "Issue created successfully" in result
            mock_create_issue.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_tool_execution_create_pull_request(self):
        """Test executing create_git_pull_request tool through server."""
        config = MCPConfig(
            enable_github_tools=True,
            forgejo_base_url="https://forgejo.example.com",
            forgejo_token="forgejo_token",
            default_git_service="forgejo",
        )
        
        with patch('doc_ai_helper_backend.services.mcp.tools.git_tools.configure_git_service'), \
             patch('doc_ai_helper_backend.services.mcp.tools.git_tools.create_git_pull_request') as mock_create_pr:
            
            mock_create_pr.return_value = "Pull request created successfully: #456"
            
            server = DocumentAIHelperMCPServer(config)
            
            # Simulate repository context
            repo_context = RepositoryContext(
                owner="owner", repo="repo", service="forgejo", ref="main", path=""
            )
            server._current_repository_context = repo_context
            
            # Execute the tool through FastMCP
            tools = server.app.get_tools()
            create_pr_tool = next(tool for tool in tools if tool.name == "create_git_pull_request")
            
            result = await create_pr_tool.handler(
                title="Test PR",
                description="This is a test PR",
                head_branch="feature-branch",
                base_branch="main",
                service_type="forgejo",
                forgejo_token="runtime_token",
            )
            
            assert "Pull request created successfully" in result
            mock_create_pr.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_tool_execution_check_permissions(self):
        """Test executing check_git_repository_permissions tool through server."""
        config = MCPConfig(
            enable_github_tools=True,
            github_token="test_token",
            default_git_service="github",
        )
        
        with patch('doc_ai_helper_backend.services.mcp.tools.git_tools.configure_git_service'), \
             patch('doc_ai_helper_backend.services.mcp.tools.git_tools.check_git_repository_permissions') as mock_check_perms:
            
            mock_check_perms.return_value = "Repository permissions: admin: True, push: True, pull: True"
            
            server = DocumentAIHelperMCPServer(config)
            
            # Simulate repository context
            repo_context = RepositoryContext(
                owner="owner", repo="repo", service="github", ref="main", path=""
            )
            server._current_repository_context = repo_context
            
            # Execute the tool through FastMCP
            tools = server.app.get_tools()
            check_perms_tool = next(tool for tool in tools if tool.name == "check_git_repository_permissions")
            
            result = await check_perms_tool.handler(
                service_type="github",
                github_token="runtime_token",
            )
            
            assert "Repository permissions" in result
            mock_check_perms.assert_called_once()

    def test_server_configuration_error_handling(self):
        """Test server handles configuration errors gracefully."""
        config = MCPConfig(
            enable_github_tools=True,
            github_token="test_token",
            default_git_service="github",
        )
        
        with patch('doc_ai_helper_backend.services.mcp.tools.git_tools.configure_git_service') as mock_configure, \
             patch('doc_ai_helper_backend.services.mcp.server.logger') as mock_logger:
            
            mock_configure.side_effect = Exception("Configuration error")
            
            # Should not raise exception, but log warning
            server = DocumentAIHelperMCPServer(config)
            
            mock_logger.warning.assert_called_with(
                "Failed to configure GitHub service: Configuration error"
            )

    def test_server_partial_configuration_success(self):
        """Test server handles partial configuration success."""
        config = MCPConfig(
            enable_github_tools=True,
            github_token="test_token",
            forgejo_base_url="https://forgejo.example.com",
            forgejo_token="forgejo_token",
            default_git_service="github",
        )
        
        def mock_configure_side_effect(service_type, *args, **kwargs):
            if service_type == "github":
                return  # Success
            elif service_type == "forgejo":
                raise Exception("Forgejo configuration error")
        
        with patch('doc_ai_helper_backend.services.mcp.tools.git_tools.configure_git_service') as mock_configure, \
             patch('doc_ai_helper_backend.services.mcp.server.logger') as mock_logger:
            
            mock_configure.side_effect = mock_configure_side_effect
            
            server = DocumentAIHelperMCPServer(config)
            
            # Should log success for GitHub and warning for Forgejo
            info_calls = [call for call in mock_logger.info.call_args_list 
                         if "Configured GitHub service" in str(call)]
            warning_calls = [call for call in mock_logger.warning.call_args_list 
                           if "Failed to configure Forgejo service" in str(call)]
            
            assert len(info_calls) == 1
            assert len(warning_calls) == 1
