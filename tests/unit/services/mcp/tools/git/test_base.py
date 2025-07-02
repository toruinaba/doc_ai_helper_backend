"""
Unit tests for MCP Git tools base classes.

Tests the abstract base classes and common functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict, List, Optional

from doc_ai_helper_backend.services.mcp.tools.git.base import (
    MCPGitClientBase,
    MCPGitToolsBase,
)
from doc_ai_helper_backend.models.repository_context import RepositoryContext


class MockGitClient(MCPGitClientBase):
    """Mock implementation of Git client for testing."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.create_issue_mock = AsyncMock()
        self.create_pull_request_mock = AsyncMock()
        self.check_repository_permissions_mock = AsyncMock()
    
    async def create_issue(
        self,
        repository: str,
        title: str,
        description: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        return await self.create_issue_mock(
            repository, title, description, labels, assignees, **kwargs
        )
    
    async def create_pull_request(
        self,
        repository: str,
        title: str,
        description: str,
        head_branch: str,
        base_branch: str = "main",
        **kwargs
    ) -> Dict[str, Any]:
        return await self.create_pull_request_mock(
            repository, title, description, head_branch, base_branch, **kwargs
        )
    
    async def check_repository_permissions(
        self,
        repository: str,
        **kwargs
    ) -> Dict[str, Any]:
        return await self.check_repository_permissions_mock(repository, **kwargs)


class MockGitTools(MCPGitToolsBase):
    """Mock implementation of Git tools for testing."""
    
    @property
    def service_name(self) -> str:
        return "mock"


class TestMCPGitClientBase:
    """Test cases for MCPGitClientBase."""
    
    def test_abstract_class_cannot_be_instantiated(self):
        """Test that the abstract base class cannot be instantiated directly."""
        with pytest.raises(TypeError):
            MCPGitClientBase()
    
    def test_mock_implementation(self):
        """Test that mock implementation can be instantiated."""
        client = MockGitClient(test_config="value")
        assert client.config == {"test_config": "value"}


class TestMCPGitToolsBase:
    """Test cases for MCPGitToolsBase."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock Git client."""
        return MockGitClient()
    
    @pytest.fixture
    def git_tools(self, mock_client):
        """Create Git tools instance with mock client."""
        return MockGitTools(mock_client)
    
    @pytest.fixture
    def repository_context(self):
        """Create a test repository context."""
        return {
            "service": "github",
            "owner": "testuser",
            "repo": "test-repo",
            "repository_full_name": "testuser/test-repo",
            "current_path": "README.md",
            "base_url": "https://github.com/testuser/test-repo",
            "ref": "main"
        }
    
    def test_abstract_class_cannot_be_instantiated(self, mock_client):
        """Test that the abstract base class cannot be instantiated directly."""
        with pytest.raises(TypeError):
            MCPGitToolsBase(mock_client)
    
    def test_mock_implementation(self, mock_client):
        """Test that mock implementation can be instantiated."""
        tools = MockGitTools(mock_client)
        assert tools.client == mock_client
        assert tools.service_name == "mock"
    
    async def test_create_issue_success(self, git_tools, mock_client, repository_context):
        """Test successful issue creation."""
        # Setup mock response
        mock_client.create_issue_mock.return_value = {
            "issue_number": 123,
            "issue_url": "https://github.com/testuser/test-repo/issues/123",
            "title": "Test Issue",
            "state": "open"
        }
        
        result = await git_tools.create_issue(
            title="Test Issue",
            description="Test description",
            labels=["bug"],
            assignees=["testuser"],
            repository_context=repository_context
        )
        
        # Verify mock was called correctly
        mock_client.create_issue_mock.assert_called_once_with(
            "testuser/test-repo",
            "Test Issue",
            "Test description",
            ["bug"],
            ["testuser"]
        )
        
        # Verify result format
        assert "success" in result
        assert "true" in result.lower()
    
    async def test_create_issue_invalid_context(self, git_tools):
        """Test issue creation with invalid repository context."""
        result = await git_tools.create_issue(
            title="Test Issue",
            description="Test description",
            repository_context=None
        )
        
        # Should return error response
        assert "success" in result
        assert "false" in result.lower()
        assert "error" in result.lower()
    
    async def test_create_issue_repository_access_validation(self, git_tools, repository_context):
        """Test repository access validation."""
        # Try to access different repository
        different_context = repository_context.copy()
        different_context["repository_full_name"] = "otheruser/other-repo"
        
        result = await git_tools.create_issue(
            title="Test Issue",
            description="Test description",
            repository_context=different_context
        )
        
        # Should return error due to repository mismatch
        assert "success" in result
        assert "false" in result.lower()
        assert "error" in result.lower()
    
    async def test_create_pull_request_success(self, git_tools, mock_client, repository_context):
        """Test successful pull request creation."""
        # Setup mock response
        mock_client.create_pull_request_mock.return_value = {
            "pr_number": 456,
            "pr_url": "https://github.com/testuser/test-repo/pull/456",
            "title": "Test PR",
            "state": "open"
        }
        
        result = await git_tools.create_pull_request(
            title="Test PR",
            description="Test PR description",
            head_branch="feature/test",
            base_branch="main",
            repository_context=repository_context
        )
        
        # Verify mock was called correctly
        mock_client.create_pull_request_mock.assert_called_once_with(
            "testuser/test-repo",
            "Test PR",
            "Test PR description",
            "feature/test",
            "main"
        )
        
        # Verify result format
        assert "success" in result
        assert "true" in result.lower()
    
    async def test_check_repository_permissions_success(self, git_tools, mock_client, repository_context):
        """Test successful repository permissions check."""
        # Setup mock response
        mock_client.check_repository_permissions_mock.return_value = {
            "can_read": True,
            "can_write": True,
            "can_admin": False
        }
        
        result = await git_tools.check_repository_permissions(
            repository_context=repository_context
        )
        
        # Verify mock was called correctly
        mock_client.check_repository_permissions_mock.assert_called_once_with(
            "testuser/test-repo"
        )
        
        # Verify result format
        assert "success" in result
        assert "true" in result.lower()
        assert "permissions" in result
    
    async def test_client_exception_handling(self, git_tools, mock_client, repository_context):
        """Test exception handling from client operations."""
        # Setup mock to raise exception
        mock_client.create_issue_mock.side_effect = Exception("Mock error")
        
        result = await git_tools.create_issue(
            title="Test Issue",
            description="Test description",
            repository_context=repository_context
        )
        
        # Should return error response
        assert "success" in result
        assert "false" in result.lower()
        assert "mock error" in result.lower()
    
    def test_validate_repository_context_valid(self, git_tools):
        """Test repository context validation with valid context."""
        context = {
            "service": "github",
            "owner": "testuser",
            "repo": "test-repo",
            "repository_full_name": "testuser/test-repo",
            "current_path": "README.md",
            "base_url": "https://github.com/testuser/test-repo",
            "ref": "main"
        }
        
        repo_context = git_tools._validate_repository_context(context)
        assert isinstance(repo_context, RepositoryContext)
        assert repo_context.repository_full_name == "testuser/test-repo"
    
    def test_validate_repository_context_none(self, git_tools):
        """Test repository context validation with None."""
        with pytest.raises(ValueError, match="Repository context is required"):
            git_tools._validate_repository_context(None)
    
    def test_validate_repository_context_invalid(self, git_tools):
        """Test repository context validation with invalid context."""
        with pytest.raises(ValueError, match="Invalid repository context"):
            git_tools._validate_repository_context({"invalid": "context"})
    
    def test_validate_repository_access_same_repo(self, git_tools):
        """Test repository access validation with same repository."""
        repo_context = RepositoryContext(
            service="github",
            owner="testuser",
            repo="test-repo",
            ref="main"
        )
        
        # Should not raise exception
        git_tools._validate_repository_access("testuser/test-repo", repo_context)
    
    def test_validate_repository_access_different_repo(self, git_tools):
        """Test repository access validation with different repository."""
        repo_context = RepositoryContext(
            service="github",
            owner="testuser",
            repo="test-repo",
            ref="main"
        )
        
        with pytest.raises(PermissionError, match="Access denied"):
            git_tools._validate_repository_access("otheruser/other-repo", repo_context)
