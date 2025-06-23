"""
Unit tests for MCP server GitHub tools integration.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from doc_ai_helper_backend.services.mcp.server import DocumentAIHelperMCPServer
from doc_ai_helper_backend.services.mcp.config import MCPConfig

pytestmark = pytest.mark.asyncio


class TestMCPServerGitHubIntegration:
    """Test class for MCP server GitHub tools integration."""

    @pytest.fixture
    def mcp_config(self):
        """Create MCP config with GitHub tools enabled."""
        return MCPConfig(
            server_name="test-mcp-server",
            enable_document_tools=False,
            enable_feedback_tools=False,
            enable_analysis_tools=False,
            enable_github_tools=True,
        )

    @pytest.fixture
    def mcp_server(self, mcp_config):
        """Create MCP server instance with GitHub tools enabled."""
        return DocumentAIHelperMCPServer(config=mcp_config)

    def test_mcp_server_github_tools_registration(self, mcp_server):
        """Test that GitHub tools are properly registered in MCP server."""
        # Check that GitHub tools are registered
        tools = mcp_server.list_tools()

        github_tool_names = [tool["name"] for tool in tools if "github" in tool["name"]]

        expected_tools = [
            "create_github_issue",
            "create_github_pull_request",
            "check_github_repository_permissions",
        ]

        for expected_tool in expected_tools:
            assert expected_tool in github_tool_names

    @patch("doc_ai_helper_backend.services.mcp.tools.github_tools.GitHubClient")
    async def test_mcp_server_create_github_issue_tool(
        self, mock_github_client, mcp_server
    ):
        """Test create_github_issue tool through MCP server."""
        # Setup mock GitHub client
        mock_client_instance = AsyncMock()
        mock_github_client.return_value = mock_client_instance

        # Mock repository permissions and issue creation
        mock_client_instance.check_repository_permissions.return_value = {
            "issues": True,
            "write": True,
        }

        mock_issue_data = {
            "number": 123,
            "html_url": "https://github.com/test/repo/issues/123",
            "url": "https://api.github.com/repos/test/repo/issues/123",
            "title": "Test Issue via MCP",
            "body": "This is a test issue created via MCP",
            "state": "open",
            "labels": [{"name": "enhancement"}],
            "assignees": [],
            "created_at": "2024-01-01T00:00:00Z",
        }
        mock_client_instance.create_issue.return_value = mock_issue_data

        # Test that the tool is registered correctly
        tools = await mcp_server.app.get_tools()
        create_issue_tool = tools.get("create_github_issue")

        assert create_issue_tool is not None
        assert create_issue_tool.name == "create_github_issue"

        # Since we can't easily test the direct tool call through FastMCP in unit tests,
        # we'll test the underlying function directly (integration test approach)
        from doc_ai_helper_backend.services.mcp.tools.github_tools import (
            create_github_issue,
        )

        result = await create_github_issue(
            repository="test/repo",
            title="Test Issue via MCP",
            description="This is a test issue created via MCP",
            labels=["enhancement"],
            assignees=[],
            github_token="test_token",
        )

        # Parse result
        result_data = json.loads(result)

        # Assertions
        assert result_data["success"] is True
        assert result_data["issue"]["number"] == 123
        assert result_data["issue"]["title"] == "Test Issue via MCP"
        assert result_data["issue"]["labels"] == ["enhancement"]

    @patch("doc_ai_helper_backend.services.mcp.tools.github_tools.GitHubClient")
    async def test_mcp_server_create_github_pr_tool(
        self, mock_github_client, mcp_server
    ):
        """Test create_github_pull_request tool through MCP server."""
        # Setup mock GitHub client
        mock_client_instance = AsyncMock()
        mock_github_client.return_value = mock_client_instance

        # Mock repository permissions and PR creation
        mock_client_instance.check_repository_permissions.return_value = {
            "pull_requests": True,
            "write": True,
        }

        mock_pr_data = {
            "number": 456,
            "html_url": "https://github.com/test/repo/pull/456",
            "url": "https://api.github.com/repos/test/repo/pulls/456",
            "title": "Test PR via MCP",
            "body": "This is a test PR created via MCP",
            "state": "open",
            "head": {"ref": "feature/mcp-test", "sha": "abc123"},
            "base": {"ref": "main", "sha": "def456"},
            "created_at": "2024-01-01T00:00:00Z",
        }
        mock_client_instance.create_pull_request.return_value = mock_pr_data

        # Test that the tool is registered correctly
        tools = await mcp_server.app.get_tools()
        create_pr_tool = tools.get("create_github_pull_request")

        assert create_pr_tool is not None
        assert create_pr_tool.name == "create_github_pull_request"

        # Test the underlying function directly
        from doc_ai_helper_backend.services.mcp.tools.github_tools import (
            create_github_pull_request,
        )

        result = await create_github_pull_request(
            repository="test/repo",
            title="Test PR via MCP",
            description="This is a test PR created via MCP",
            head_branch="feature/mcp-test",
            base_branch="main",
            github_token="test_token",
        )

        # Parse result
        result_data = json.loads(result)

        # Assertions
        assert result_data["success"] is True
        assert result_data["pull_request"]["number"] == 456
        assert result_data["pull_request"]["title"] == "Test PR via MCP"
        assert result_data["pull_request"]["head"]["branch"] == "feature/mcp-test"

    @patch("doc_ai_helper_backend.services.mcp.tools.github_tools.GitHubClient")
    async def test_mcp_server_check_permissions_tool(
        self, mock_github_client, mcp_server
    ):
        """Test check_github_repository_permissions tool through MCP server."""
        # Setup mock GitHub client
        mock_client_instance = AsyncMock()
        mock_github_client.return_value = mock_client_instance

        # Mock repository permissions and info
        mock_permissions = {
            "admin": False,
            "push": True,
            "pull": True,
            "issues": True,
            "pull_requests": True,
            "write": True,
        }
        mock_client_instance.check_repository_permissions.return_value = (
            mock_permissions
        )

        mock_repo_info = {
            "name": "repo",
            "full_name": "test/repo",
            "private": False,
            "has_issues": True,
            "has_projects": True,
            "has_wiki": True,
            "default_branch": "main",
        }
        mock_client_instance.get_repository_info.return_value = mock_repo_info

        # Test that the tool is registered correctly
        tools = await mcp_server.app.get_tools()
        check_permissions_tool = tools.get("check_github_repository_permissions")

        assert check_permissions_tool is not None
        assert check_permissions_tool.name == "check_github_repository_permissions"

        # Test the underlying function directly
        from doc_ai_helper_backend.services.mcp.tools.github_tools import (
            check_github_repository_permissions,
        )

        result = await check_github_repository_permissions(
            repository="test/repo",
            github_token="test_token",
        )

        # Parse result
        result_data = json.loads(result)

        # Assertions
        assert result_data["success"] is True
        assert result_data["repository"] == "test/repo"
        assert result_data["permissions"]["write"] is True
        assert result_data["repository_info"]["has_issues"] is True

    def test_mcp_server_github_tools_disabled(self):
        """Test MCP server with GitHub tools disabled."""
        config = MCPConfig(
            server_name="test-mcp-server",
            enable_document_tools=True,
            enable_feedback_tools=True,
            enable_analysis_tools=True,
            enable_github_tools=False,  # Disabled
        )

        server = DocumentAIHelperMCPServer(config=config)
        tools = server.list_tools()

        github_tool_names = [tool["name"] for tool in tools if "github" in tool["name"]]

        # Should have no GitHub tools
        assert len(github_tool_names) == 0

    def test_mcp_server_all_tools_enabled(self):
        """Test MCP server with all tools enabled including GitHub."""
        config = MCPConfig(
            server_name="test-mcp-server",
            enable_document_tools=True,
            enable_feedback_tools=True,
            enable_analysis_tools=True,
            enable_github_tools=True,
        )

        server = DocumentAIHelperMCPServer(config=config)
        tools = server.list_tools()

        tool_names = [tool["name"] for tool in tools]

        # Should have tools from all categories
        expected_github_tools = [
            "create_github_issue",
            "create_github_pull_request",
            "check_github_repository_permissions",
        ]

        for tool_name in expected_github_tools:
            assert tool_name in tool_names

        # Should also have other tools (not exhaustive check)
        assert any("document" in name for name in tool_names)
        assert any("feedback" in name for name in tool_names)
        assert any(
            "analyze" in name or "extract" in name or "check" in name
            for name in tool_names
        )  # Analysis tools

    async def test_mcp_server_github_error_handling(self, mcp_server):
        """Test error handling in GitHub tools through MCP server."""
        # Test that the tool is registered correctly
        tools = await mcp_server.app.get_tools()
        create_issue_tool = tools.get("create_github_issue")

        assert create_issue_tool is not None

        # Test the underlying function directly with invalid input
        from doc_ai_helper_backend.services.mcp.tools.github_tools import (
            create_github_issue,
        )

        result = await create_github_issue(
            repository="invalid-repo-format",  # Missing owner/repo format
            title="Test Issue",
            description="Test description",
        )

        # Parse result
        result_data = json.loads(result)

        # Should return error response
        assert result_data["success"] is False
        assert result_data["error_type"] == "validation_error"
        assert "Invalid repository format" in result_data["error"]
