"""
Integration tests for API endpoints with unified Git tools.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from doc_ai_helper_backend.main import app
from doc_ai_helper_backend.models.repository_context import RepositoryContext


class TestAPIGitToolsIntegration:
    """Integration tests for API endpoints with Git tools."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    @pytest.mark.asyncio
    async def test_llm_query_with_git_issue_creation(self):
        """Test LLM query that creates a Git issue through function calling."""
        # Mock the LLM service to return a function call
        mock_response = {
            "message": "I'll create an issue for the documentation improvement.",
            "function_calls": [
                {
                    "name": "create_git_issue",
                    "arguments": {
                        "title": "Improve README.md structure",
                        "description": "The current README structure needs improvement for better readability.",
                        "labels": ["documentation", "improvement"],
                        "service_type": "github",
                    }
                }
            ]
        }
        
        with patch('doc_ai_helper_backend.services.llm.openai_service.OpenAIService.query') as mock_query, \
             patch('doc_ai_helper_backend.services.mcp.tools.git_tools.create_git_issue') as mock_create_issue:
            
            mock_query.return_value = mock_response
            mock_create_issue.return_value = "Issue created successfully: #123 - https://github.com/owner/repo/issues/123"
            
            # Set up repository context
            repo_context = RepositoryContext(
                owner="owner", repo="repo", service="github", ref="main", path=""
            )
            
            response = self.client.post(
                "/api/v1/llm/query",
                json={
                    "prompt": "The README.md file structure is confusing. Can you create an issue to improve it?",
                    "repository_context": repo_context.dict(),
                    "enable_function_calling": True,
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "function_calls" in data
            assert len(data["function_calls"]) == 1
            assert data["function_calls"][0]["name"] == "create_git_issue"
            assert "Issue created successfully" in data["function_calls"][0]["result"]

    @pytest.mark.asyncio
    async def test_llm_stream_with_git_pr_creation(self):
        """Test LLM streaming query that creates a Git pull request."""
        # Mock the streaming LLM service
        async def mock_stream_query(*args, **kwargs):
            yield "I'll create a pull request for the fix.\n"
            yield "Function call: create_git_pull_request\n"
            yield "Result: Pull request created successfully: #456"
        
        with patch('doc_ai_helper_backend.services.llm.openai_service.OpenAIService.stream_query') as mock_stream, \
             patch('doc_ai_helper_backend.services.mcp.tools.git_tools.create_git_pull_request') as mock_create_pr:
            
            mock_stream.return_value = mock_stream_query()
            mock_create_pr.return_value = "Pull request created successfully: #456 - https://github.com/owner/repo/pull/456"
            
            # Set up repository context
            repo_context = RepositoryContext(
                owner="owner", repo="repo", service="github", ref="main", path=""
            )
            
            response = self.client.post(
                "/api/v1/llm/stream",
                json={
                    "prompt": "Create a pull request to fix the typo in line 25 of README.md",
                    "repository_context": repo_context.dict(),
                    "enable_function_calling": True,
                }
            )
            
            assert response.status_code == 200
            
            # Collect streaming response
            content = ""
            for line in response.iter_lines():
                if line:
                    content += line.decode() + "\n"
            
            assert "create_git_pull_request" in content
            assert "Pull request created successfully" in content

    @pytest.mark.asyncio
    async def test_mcp_tools_endpoint_git_operations(self):
        """Test MCP tools endpoint for Git operations."""
        with patch('doc_ai_helper_backend.services.mcp.tools.git_tools.create_git_issue') as mock_create_issue:
            mock_create_issue.return_value = "Issue created successfully: #789"
            
            response = self.client.post(
                "/api/v1/mcp/tools/call",
                json={
                    "tool_name": "create_git_issue",
                    "arguments": {
                        "title": "Test Issue",
                        "description": "This is a test issue",
                        "labels": ["test"],
                        "service_type": "github",
                        "github_token": "test_token",
                    }
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "Issue created successfully" in data["result"]
            mock_create_issue.assert_called_once()

    @pytest.mark.asyncio
    async def test_mcp_tools_endpoint_forgejo_operations(self):
        """Test MCP tools endpoint for Forgejo operations."""
        with patch('doc_ai_helper_backend.services.mcp.tools.git_tools.create_git_pull_request') as mock_create_pr:
            mock_create_pr.return_value = "Pull request created successfully: #101"
            
            response = self.client.post(
                "/api/v1/mcp/tools/call",
                json={
                    "tool_name": "create_git_pull_request",
                    "arguments": {
                        "title": "Test PR",
                        "description": "This is a test PR",
                        "head_branch": "feature-branch",
                        "base_branch": "main",
                        "service_type": "forgejo",
                        "forgejo_token": "forgejo_token",
                    }
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "Pull request created successfully" in data["result"]
            mock_create_pr.assert_called_once()

    @pytest.mark.asyncio
    async def test_mcp_tools_list_includes_git_tools(self):
        """Test that MCP tools list includes unified Git tools."""
        response = self.client.get("/api/v1/mcp/tools")
        
        assert response.status_code == 200
        data = response.json()
        
        tool_names = [tool["name"] for tool in data["tools"]]
        
        # Should include unified Git tools
        assert "create_git_issue" in tool_names
        assert "create_git_pull_request" in tool_names
        assert "check_git_repository_permissions" in tool_names
        
        # Should NOT include legacy GitHub-specific tools
        assert "create_github_issue" not in tool_names
        assert "create_github_pull_request" not in tool_names

    @pytest.mark.asyncio
    async def test_mcp_tools_endpoint_permissions_check(self):
        """Test MCP tools endpoint for permissions check."""
        with patch('doc_ai_helper_backend.services.mcp.tools.git_tools.check_git_repository_permissions') as mock_check_perms:
            mock_check_perms.return_value = "Repository permissions: admin: True, push: True, pull: True"
            
            response = self.client.post(
                "/api/v1/mcp/tools/call",
                json={
                    "tool_name": "check_git_repository_permissions",
                    "arguments": {
                        "service_type": "github",
                        "github_token": "test_token",
                    }
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "Repository permissions" in data["result"]
            mock_check_perms.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_for_unsupported_git_service(self):
        """Test error handling for unsupported Git service."""
        response = self.client.post(
            "/api/v1/mcp/tools/call",
            json={
                "tool_name": "create_git_issue",
                "arguments": {
                    "title": "Test Issue",
                    "description": "This is a test issue",
                    "service_type": "gitlab",  # Unsupported service
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return error result rather than throwing exception
        assert "error" in data or "Unsupported service type" in str(data)

    @pytest.mark.asyncio
    async def test_configuration_based_service_selection(self):
        """Test that configuration-based service selection works."""
        # Mock configuration to prefer Forgejo
        mock_config = Mock()
        mock_config.default_git_service = "forgejo"
        mock_config.enable_github_tools = True
        mock_config.forgejo_base_url = "https://forgejo.example.com"
        mock_config.forgejo_token = "forgejo_token"
        
        with patch('doc_ai_helper_backend.services.mcp.tools.git_tools._default_service', "forgejo"), \
             patch('doc_ai_helper_backend.services.mcp.tools.git_tools.create_git_issue') as mock_create_issue:
            
            mock_create_issue.return_value = "Issue created successfully on Forgejo: #42"
            
            response = self.client.post(
                "/api/v1/mcp/tools/call",
                json={
                    "tool_name": "create_git_issue",
                    "arguments": {
                        "title": "Test Issue",
                        "description": "This is a test issue",
                        # No explicit service_type - should use configured default
                    }
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "Issue created successfully" in data["result"]
            mock_create_issue.assert_called_once()

    @pytest.mark.asyncio
    async def test_runtime_credentials_override_configuration(self):
        """Test that runtime credentials can override configuration."""
        with patch('doc_ai_helper_backend.services.mcp.tools.git_tools.create_git_issue') as mock_create_issue:
            mock_create_issue.return_value = "Issue created with runtime credentials: #999"
            
            response = self.client.post(
                "/api/v1/mcp/tools/call",
                json={
                    "tool_name": "create_git_issue",
                    "arguments": {
                        "title": "Test Issue",
                        "description": "This is a test issue",
                        "service_type": "github",
                        "github_token": "runtime_override_token",  # Runtime credential
                    }
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "Issue created" in data["result"]
            
            # Verify that runtime credentials were used
            call_args = mock_create_issue.call_args
            assert "github_token" in call_args.kwargs
            assert call_args.kwargs["github_token"] == "runtime_override_token"
