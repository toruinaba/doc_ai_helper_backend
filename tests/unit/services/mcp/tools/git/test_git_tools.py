"""
Unit tests for unified Git tools.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from doc_ai_helper_backend.services.mcp.tools.git_tools import (
    configure_git_service,
    create_git_issue,
    create_git_pull_request,
    check_git_repository_permissions,
    _configured_services,
    _default_service,
)
from doc_ai_helper_backend.models.repository_context import RepositoryContext


class TestGitToolsConfiguration:
    """Test cases for Git tools configuration."""

    def teardown_method(self):
        """Clean up after each test."""
        # Clear configured services
        _configured_services.clear()
        global _default_service
        _default_service = None

    def test_configure_github_service(self):
        """Test configuring GitHub service."""
        config = {"access_token": "test_token", "default_labels": ["bug"]}
        
        configure_git_service("github", config, set_as_default=True)
        
        assert "github" in _configured_services
        assert _default_service == "github"
        assert _configured_services["github"].config == config

    def test_configure_forgejo_service(self):
        """Test configuring Forgejo service."""
        config = {
            "base_url": "https://forgejo.example.com",
            "access_token": "test_token",
            "default_labels": ["enhancement"],
        }
        
        configure_git_service("forgejo", config, set_as_default=False)
        
        assert "forgejo" in _configured_services
        assert _default_service is None  # Not set as default
        assert _configured_services["forgejo"].config == config

    def test_configure_invalid_service_type_raises_error(self):
        """Test that configuring invalid service type raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported service type"):
            configure_git_service("gitlab", {"access_token": "test"})

    def test_configure_multiple_services(self):
        """Test configuring multiple services."""
        github_config = {"access_token": "github_token"}
        forgejo_config = {
            "base_url": "https://forgejo.example.com",
            "access_token": "forgejo_token",
        }
        
        configure_git_service("github", github_config, set_as_default=True)
        configure_git_service("forgejo", forgejo_config, set_as_default=False)
        
        assert len(_configured_services) == 2
        assert "github" in _configured_services
        assert "forgejo" in _configured_services
        assert _default_service == "github"


class TestGitToolsOperations:
    """Test cases for Git tools operations."""

    def teardown_method(self):
        """Clean up after each test."""
        # Clear configured services
        _configured_services.clear()
        global _default_service
        _default_service = None

    @pytest.mark.asyncio
    async def test_create_issue_with_default_service(self):
        """Test creating issue with default service."""
        # Configure GitHub as default service
        github_config = {"access_token": "test_token"}
        configure_git_service("github", github_config, set_as_default=True)
        
        repo_context = RepositoryContext(
            owner="owner", repo="repo", service="github", ref="main", path=""
        )
        
        # Mock the adapter
        mock_adapter = Mock()
        mock_adapter.create_issue = AsyncMock(return_value="Issue created successfully: #123")
        _configured_services["github"] = mock_adapter
        
        result = await create_git_issue(
            title="Test Issue",
            description="This is a test issue",
            repository_context=repo_context,
        )
        
        assert "Issue created successfully" in result
        mock_adapter.create_issue.assert_called_once_with(
            title="Test Issue",
            description="This is a test issue",
            labels=None,
            assignees=None,
            repository_context=repo_context,
        )

    @pytest.mark.asyncio
    async def test_create_issue_with_explicit_service_type(self):
        """Test creating issue with explicit service type."""
        # Configure both GitHub and Forgejo
        github_config = {"access_token": "github_token"}
        forgejo_config = {
            "base_url": "https://forgejo.example.com",
            "access_token": "forgejo_token",
        }
        configure_git_service("github", github_config, set_as_default=True)
        configure_git_service("forgejo", forgejo_config, set_as_default=False)
        
        repo_context = RepositoryContext(
            owner="owner", repo="repo", service="forgejo", ref="main", path=""
        )
        
        # Mock the adapters
        mock_github_adapter = Mock()
        mock_forgejo_adapter = Mock()
        mock_forgejo_adapter.create_issue = AsyncMock(return_value="Issue created successfully: #456")
        _configured_services["github"] = mock_github_adapter
        _configured_services["forgejo"] = mock_forgejo_adapter
        
        result = await create_git_issue(
            title="Test Issue",
            description="This is a test issue",
            repository_context=repo_context,
            service_type="forgejo",
        )
        
        assert "Issue created successfully" in result
        # Forgejo adapter should be called, not GitHub
        mock_forgejo_adapter.create_issue.assert_called_once()
        mock_github_adapter.create_issue.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_issue_with_runtime_credentials(self):
        """Test creating issue with runtime credentials."""
        repo_context = RepositoryContext(
            owner="owner", repo="repo", service="github", ref="main", path=""
        )
        
        # No pre-configured services, should create temporary service
        with patch('doc_ai_helper_backend.services.mcp.tools.git.factory.MCPGitToolsFactory.create_adapter') as mock_create:
            mock_adapter = Mock()
            mock_adapter.create_issue = AsyncMock(return_value="Issue created successfully: #789")
            mock_create.return_value = mock_adapter
            
            result = await create_git_issue(
                title="Test Issue",
                description="This is a test issue",
                repository_context=repo_context,
                service_type="github",
                github_token="runtime_token",
            )
            
            assert "Issue created successfully" in result
            mock_create.assert_called_once_with("github", {"access_token": "runtime_token"})
            mock_adapter.create_issue.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_issue_without_service_or_context_raises_error(self):
        """Test that creating issue without service or context raises error."""
        with pytest.raises(ValueError, match="No Git service configured"):
            await create_git_issue(
                title="Test Issue",
                description="This is a test issue",
            )

    @pytest.mark.asyncio
    async def test_create_pull_request_with_default_service(self):
        """Test creating pull request with default service."""
        # Configure GitHub as default service
        github_config = {"access_token": "test_token"}
        configure_git_service("github", github_config, set_as_default=True)
        
        repo_context = RepositoryContext(
            owner="owner", repo="repo", service="github", ref="main", path=""
        )
        
        # Mock the adapter
        mock_adapter = Mock()
        mock_adapter.create_pull_request = AsyncMock(return_value="PR created successfully: #123")
        _configured_services["github"] = mock_adapter
        
        result = await create_git_pull_request(
            title="Test PR",
            description="This is a test PR",
            head_branch="feature-branch",
            base_branch="main",
            repository_context=repo_context,
        )
        
        assert "PR created successfully" in result
        mock_adapter.create_pull_request.assert_called_once_with(
            title="Test PR",
            description="This is a test PR",
            head_branch="feature-branch",
            base_branch="main",
            repository_context=repo_context,
        )

    @pytest.mark.asyncio
    async def test_check_repository_permissions_with_forgejo_runtime_credentials(self):
        """Test checking repository permissions with Forgejo runtime credentials."""
        repo_context = RepositoryContext(
            owner="owner", repo="repo", service="forgejo", ref="main", path=""
        )
        
        # No pre-configured services, should create temporary service
        with patch('doc_ai_helper_backend.services.mcp.tools.git.factory.MCPGitToolsFactory.create_adapter') as mock_create:
            mock_adapter = Mock()
            mock_adapter.check_repository_permissions = AsyncMock(
                return_value="Repository permissions: admin: True, push: True, pull: True"
            )
            mock_create.return_value = mock_adapter
            
            result = await check_git_repository_permissions(
                repository_context=repo_context,
                service_type="forgejo",
                forgejo_token="runtime_token",
            )
            
            assert "Repository permissions" in result
            mock_create.assert_called_once_with("forgejo", {"access_token": "runtime_token"})
            mock_adapter.check_repository_permissions.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_permissions_with_forgejo_username_password(self):
        """Test checking permissions with Forgejo username/password."""
        repo_context = RepositoryContext(
            owner="owner", repo="repo", service="forgejo", ref="main", path=""
        )
        
        with patch('doc_ai_helper_backend.services.mcp.tools.git.factory.MCPGitToolsFactory.create_adapter') as mock_create:
            mock_adapter = Mock()
            mock_adapter.check_repository_permissions = AsyncMock(
                return_value="Repository permissions: admin: False, push: True, pull: True"
            )
            mock_create.return_value = mock_adapter
            
            result = await check_git_repository_permissions(
                repository_context=repo_context,
                service_type="forgejo",
                forgejo_username="testuser",
                forgejo_password="testpass",
            )
            
            assert "Repository permissions" in result
            expected_config = {
                "username": "testuser",
                "password": "testpass",
            }
            mock_create.assert_called_once_with("forgejo", expected_config)

    @pytest.mark.asyncio
    async def test_operation_with_unsupported_service_raises_error(self):
        """Test that operations with unsupported service raise error."""
        repo_context = RepositoryContext(
            owner="owner", repo="repo", service="gitlab", ref="main", path=""
        )
        
        with pytest.raises(ValueError, match="Unsupported service type"):
            await create_git_issue(
                title="Test Issue",
                description="This is a test issue",
                repository_context=repo_context,
                service_type="gitlab",
            )

    @pytest.mark.asyncio
    async def test_operation_error_handling(self):
        """Test error handling in operations."""
        # Configure GitHub service
        github_config = {"access_token": "test_token"}
        configure_git_service("github", github_config, set_as_default=True)
        
        repo_context = RepositoryContext(
            owner="owner", repo="repo", service="github", ref="main", path=""
        )
        
        # Mock the adapter to raise an exception
        mock_adapter = Mock()
        mock_adapter.create_issue = AsyncMock(side_effect=Exception("API Error"))
        _configured_services["github"] = mock_adapter
        
        result = await create_git_issue(
            title="Test Issue",
            description="This is a test issue",
            repository_context=repo_context,
        )
        
        assert "Error creating issue" in result
        assert "API Error" in result
