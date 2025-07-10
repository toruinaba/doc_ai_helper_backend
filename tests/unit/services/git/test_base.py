"""
Test for Git service base functionality.

This module contains unit tests for the GitServiceBase abstract class.
"""

import pytest
from abc import ABC
from unittest.mock import Mock, patch

from doc_ai_helper_backend.services.git.base import GitServiceBase
from doc_ai_helper_backend.core.exceptions import (
    GitServiceException,
    NotFoundException,
    RateLimitException,
    UnauthorizedException,
)


class ConcreteGitService(GitServiceBase):
    """Concrete implementation of GitServiceBase for testing."""

    def _get_service_name(self) -> str:
        return "test_service"

    def get_supported_auth_methods(self) -> list:
        return ["token", "basic"]

    async def authenticate(self) -> bool:
        return True

    async def get_rate_limit_info(self) -> dict:
        return {"remaining": 100, "limit": 5000}

    async def test_connection(self) -> dict:
        return {"status": "ok", "service": "test_service"}

    async def get_document(
        self, owner: str, repo: str, path: str, ref: str = "main"
    ) -> dict:
        return {"content": "test content", "path": path, "owner": owner, "repo": repo}

    async def get_repository_structure(
        self, owner: str, repo: str, ref: str = "main", path: str = ""
    ) -> dict:
        return {"type": "dir", "entries": [], "owner": owner, "repo": repo}

    async def search_repository(
        self, owner: str, repo: str, query: str, limit: int = 10
    ) -> list:
        return [{"name": "result1", "path": "path1"}]

    async def check_repository_exists(self, owner: str, repo: str) -> bool:
        return True

    async def get_file_content(
        self, owner: str, repo: str, path: str, ref: str = "main"
    ) -> dict:
        return {"content": "test content", "path": path}

    async def get_repository_info(self, owner: str, repo: str) -> dict:
        return {"name": repo, "owner": owner}


class TestGitServiceBase:
    """Test the Git service base functionality."""

    @pytest.fixture
    def git_service(self):
        """Create a concrete Git service instance for testing."""
        return ConcreteGitService(
            access_token="test_token", base_url="https://test.com"
        )

    def test_initialization_with_token(self):
        """Test GitServiceBase initialization with access token."""
        service = ConcreteGitService(access_token="test_token")

        assert service.access_token == "test_token"
        assert service.service_name == "test_service"
        assert isinstance(service.config, dict)

    def test_initialization_without_token(self):
        """Test GitServiceBase initialization without access token."""
        service = ConcreteGitService()

        assert service.access_token is None
        assert service.service_name == "test_service"

    def test_initialization_with_kwargs(self):
        """Test GitServiceBase initialization with additional configuration."""
        service = ConcreteGitService(
            access_token="test_token", base_url="https://custom.com", timeout=30
        )

        assert service.access_token == "test_token"
        assert service.config["base_url"] == "https://custom.com"
        assert service.config["timeout"] == 30

    def test_service_name_property(self, git_service):
        """Test service name property."""
        assert git_service.service_name == "test_service"

    def test_abstract_methods_must_be_implemented(self):
        """Test that abstract methods must be implemented."""
        with pytest.raises(TypeError):
            GitServiceBase()  # Cannot instantiate abstract class

    def test_supported_auth_methods(self, git_service):
        """Test supported authentication methods."""
        auth_methods = git_service.get_supported_auth_methods()

        assert isinstance(auth_methods, list)
        assert "token" in auth_methods
        assert "basic" in auth_methods

    @pytest.mark.asyncio
    async def test_get_file_content_interface(self, git_service):
        """Test get_file_content interface."""
        result = await git_service.get_file_content("owner", "repo", "test.md")

        assert isinstance(result, dict)
        assert "content" in result
        assert "path" in result

    @pytest.mark.asyncio
    async def test_get_repository_structure_interface(self, git_service):
        """Test get_repository_structure interface."""
        result = await git_service.get_repository_structure("owner", "repo")

        assert isinstance(result, dict)
        assert "type" in result
        assert "entries" in result

    @pytest.mark.asyncio
    async def test_get_repository_info_interface(self, git_service):
        """Test get_repository_info interface."""
        result = await git_service.get_repository_info("owner", "repo")

        assert isinstance(result, dict)
        assert "name" in result
        assert "owner" in result

    def test_config_property(self, git_service):
        """Test config property access."""
        assert hasattr(git_service, "config")
        assert isinstance(git_service.config, dict)

    def test_access_token_property(self, git_service):
        """Test access_token property access."""
        assert hasattr(git_service, "access_token")
        assert git_service.access_token == "test_token"

    def test_git_service_is_abstract(self):
        """Test that GitServiceBase is an abstract base class."""
        assert issubclass(GitServiceBase, ABC)
        assert GitServiceBase.__abstractmethods__  # Has abstract methods

    def test_concrete_implementation_works(self):
        """Test that concrete implementation works correctly."""
        service = ConcreteGitService(access_token="test")

        # Should be able to instantiate and use
        assert service.service_name == "test_service"
        assert service.get_supported_auth_methods() == ["token", "basic"]

    def test_multiple_instances_are_independent(self):
        """Test that multiple instances are independent."""
        service1 = ConcreteGitService(access_token="token1", custom_config="config1")
        service2 = ConcreteGitService(access_token="token2", custom_config="config2")

        assert service1.access_token == "token1"
        assert service2.access_token == "token2"
        assert service1.config["custom_config"] == "config1"
        assert service2.config["custom_config"] == "config2"
