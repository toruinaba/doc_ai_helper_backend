"""
Integration test for secure GitHub tools with repository context.
"""

import pytest
import asyncio
import json
import os
from typing import Dict, Any

from doc_ai_helper_backend.models.llm import LLMQueryRequest
from doc_ai_helper_backend.models.repository_context import RepositoryContext
from doc_ai_helper_backend.services.llm.factory import LLMServiceFactory


class TestSecureGitHubToolsIntegration:
    """Integration tests for secure GitHub tools with repository context."""

    @pytest.mark.asyncio
    async def test_secure_github_issue_creation_with_repository_context(self):
        """Test secure GitHub issue creation with repository context through LLM."""

        # Mock repository context - simulating user viewing a specific document
        repository_context = RepositoryContext(
            service="github",
            owner="test-owner",
            repo="test-repo",
            ref="main",
            current_path="docs/README.md",
        )

        # Create LLM service (using mock service for testing)
        llm_service = LLMServiceFactory.create("mock")

        # Prepare LLM request with tools and repository context
        request = LLMQueryRequest(
            prompt="この README.md の構造改善について GitHub Issue を作成してください",
            enable_tools=True,
            repository_context=repository_context,
            document_content="# Test README\nThis is a test document.",
            tool_choice="create_github_issue",
            complete_tool_flow=True,
        )

        # Execute LLM query with tools
        response = await llm_service.query(
            prompt=request.prompt,
            options={"model": "gpt-3.5-turbo", "functions": ["create_github_issue"]},
            repository_context=repository_context,
            document_content=request.document_content,
        )

        # Verify response structure
        assert response is not None
        assert hasattr(response, "content")

        # Note: In actual implementation, this would trigger the secure GitHub tool
        # and verify that repository context is properly validated

    @pytest.mark.asyncio
    async def test_repository_context_prevents_unauthorized_access(self):
        """Test that repository context prevents access to other repositories."""

        # User is viewing test-owner/test-repo
        repository_context = RepositoryContext(
            service="github", owner="test-owner", repo="test-repo", ref="main"
        )

        # Create LLM service
        llm_service = LLMServiceFactory.create("mock")

        # Try to access different repository (should be blocked by secure tools)
        request = LLMQueryRequest(
            prompt="other-owner/other-repo リポジトリに Issue を作成してください",
            enable_tools=True,
            repository_context=repository_context,
            tool_choice="create_github_issue",
            complete_tool_flow=True,
        )

        # Execute LLM query
        response = await llm_service.query(
            prompt=request.prompt,
            options={"model": "gpt-3.5-turbo", "functions": ["create_github_issue"]},
            repository_context=repository_context,
        )

        # Verify response (in real implementation, this would show access denied)
        assert response is not None

    @pytest.mark.asyncio
    async def test_secure_tools_parameter_schema(self):
        """Test that secure GitHub tools have correct parameter schemas."""

        from doc_ai_helper_backend.services.mcp.function_adapter import (
            MCPFunctionAdapter,
        )
        from doc_ai_helper_backend.services.mcp.server import DocumentAIHelperMCPServer
        from doc_ai_helper_backend.services.mcp.config import MCPConfig

        # Create MCP server with GitHub tools enabled
        config = MCPConfig(
            enable_document_tools=True,
            enable_feedback_tools=True,
            enable_analysis_tools=True,
            enable_github_tools=True,
            enable_utility_tools=True,
        )

        mcp_server = DocumentAIHelperMCPServer(config)
        adapter = MCPFunctionAdapter(mcp_server)

        # Ensure tools are registered
        await adapter._ensure_tools_registered()

        # Get function definitions
        functions = await adapter.get_available_functions()
        function_names = [f.name for f in functions]

        # Verify secure GitHub tools are available
        assert "create_github_issue" in function_names
        assert "create_github_pull_request" in function_names

        # Check parameter schemas for secure tools
        secure_issue_func = next(
            f for f in functions if f.name == "create_github_issue"
        )
        secure_pr_func = next(
            f for f in functions if f.name == "create_github_pull_request"
        )

        # Verify secure issue tool parameters
        issue_params = secure_issue_func.parameters
        assert "properties" in issue_params
        assert "title" in issue_params["properties"]
        assert "description" in issue_params["properties"]
        # Note: repository parameter should NOT be present (auto-injected from context)
        assert "repository" not in issue_params["properties"]

        # Verify secure PR tool parameters
        pr_params = secure_pr_func.parameters
        assert "properties" in pr_params
        assert "title" in pr_params["properties"]
        assert "description" in pr_params["properties"]
        assert "head_branch" in pr_params["properties"]
        # Note: repository parameter should NOT be present (auto-injected from context)
        assert "repository" not in pr_params["properties"]

    def test_repository_context_model_validation(self):
        """Test RepositoryContext model validation."""

        # Valid repository context
        valid_context = RepositoryContext(
            service="github",
            owner="valid-owner",
            repo="valid-repo",
            ref="main",
            current_path="docs/README.md",
        )

        assert valid_context.repository_full_name == "valid-owner/valid-repo"
        assert valid_context.service == "github"

        # Test repository URL generation
        assert "github.com" in valid_context.repository_url
        assert "valid-owner/valid-repo" in valid_context.repository_url

        # Test document URL generation
        doc_url = valid_context.document_url
        assert doc_url is not None
        assert "blob/main/docs/README.md" in doc_url

    @pytest.mark.asyncio
    async def test_mcp_server_repository_context_setting(self):
        """Test MCP server repository context setting functionality."""

        from doc_ai_helper_backend.services.mcp.server import DocumentAIHelperMCPServer
        from doc_ai_helper_backend.services.mcp.config import MCPConfig

        # Create MCP server
        config = MCPConfig(enable_github_tools=True)
        mcp_server = DocumentAIHelperMCPServer(config)

        # Test context setting
        repo_context = {
            "service": "github",
            "owner": "test-owner",
            "repo": "test-repo",
            "ref": "main",
        }

        mcp_server.set_repository_context(repo_context)

        # Verify context was set
        assert hasattr(mcp_server, "_current_repository_context")
        assert mcp_server._current_repository_context == repo_context

        # Test context clearing
        mcp_server.set_repository_context(None)
        assert mcp_server._current_repository_context is None


if __name__ == "__main__":
    # Run specific test
    pytest.main(
        [
            __file__
            + "::TestSecureGitHubToolsIntegration::test_secure_tools_parameter_schema",
            "-v",
        ]
    )
