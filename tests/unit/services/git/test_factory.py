"""
Unit tests for Git service factory.

This module contains tests for the GitServiceFactory class that manages
Git service registration and instantiation.
"""

import pytest
from unittest.mock import patch, MagicMock

from doc_ai_helper_backend.core.exceptions import GitServiceException
from doc_ai_helper_backend.services.git.factory import GitServiceFactory
from doc_ai_helper_backend.services.git.base import GitServiceBase
from doc_ai_helper_backend.services.git.github_service import GitHubService
from doc_ai_helper_backend.services.git.forgejo_service import ForgejoService
from doc_ai_helper_backend.services.git.mock_service import MockGitService


class DummyGitService(GitServiceBase):
    """Dummy Git service for testing."""

    def __init__(self, access_token: str = None, **kwargs):
        super().__init__(access_token=access_token)
        self.config = kwargs

    def _get_service_name(self) -> str:
        """Get service name."""
        return "dummy"

    def get_supported_auth_methods(self) -> list:
        """Get supported authentication methods."""
        return ["token"]

    async def get_repository_structure(
        self, owner: str, repo: str, path: str = "", ref: str = "main"
    ):
        """Dummy repository structure method."""
        return {"files": [], "directories": []}

    async def authenticate(self):
        """Dummy authenticate method."""
        return True

    async def check_repository_exists(self, owner: str, repo: str) -> bool:
        """Dummy repository check."""
        return True

    async def get_document(self, owner: str, repo: str, path: str, ref: str = "main"):
        """Dummy get document method."""
        return {"content": "dummy content"}

    async def get_rate_limit_info(self):
        """Dummy rate limit info."""
        return {"limit": 5000, "remaining": 5000}

    async def search_repository(self, query: str, **kwargs):
        """Dummy search method."""
        return []

    async def test_connection(self) -> bool:
        """Dummy connection test."""
        return True


class TestGitServiceFactory:
    """Test the Git service factory."""

    def setup_method(self):
        """Set up test fixtures."""
        # Reset the factory registry to original state
        GitServiceFactory._services = {
            "github": GitHubService,
            "forgejo": ForgejoService,
            "mock": MockGitService,
        }

    def test_create_github_service(self):
        """Test creating GitHub service."""
        service = GitServiceFactory.create("github", access_token="test_token")
        assert isinstance(service, GitHubService)
        assert service.access_token == "test_token"

    def test_create_mock_service(self):
        """Test creating mock service."""
        service = GitServiceFactory.create("mock", access_token="test_token")
        assert isinstance(service, MockGitService)
        assert service.access_token == "test_token"

    def test_create_forgejo_service(self):
        """Test creating Forgejo service with explicit base_url."""
        service = GitServiceFactory.create(
            "forgejo", access_token="test_token", base_url="https://forgejo.example.com"
        )
        assert isinstance(service, ForgejoService)
        assert service.access_token == "test_token"

    def test_create_forgejo_service_with_base_url(self):
        """Test creating Forgejo service with explicit base_url."""
        service = GitServiceFactory.create(
            "forgejo", access_token="test_token", base_url="https://forgejo.custom.com"
        )
        assert isinstance(service, ForgejoService)
        assert service.access_token == "test_token"

    def test_create_with_additional_kwargs(self):
        """Test creating service with additional configuration."""
        service = GitServiceFactory.create(
            "mock", access_token="test_token", base_url="https://custom.com", timeout=30
        )
        assert isinstance(service, MockGitService)
        assert service.access_token == "test_token"
        # Note: MockGitService doesn't use config, so we can't test base_url storage

    def test_create_unknown_service_raises_exception(self):
        """Test creating service with unknown type raises exception."""
        with pytest.raises(GitServiceException) as exc_info:
            GitServiceFactory.create("unknown_service")

        assert "Unsupported Git service: unknown_service" in str(exc_info.value)

    def test_register_new_service(self):
        """Test registering a new service."""
        # Register dummy service
        GitServiceFactory.register_service("dummy", DummyGitService)

        # Verify it was registered
        assert "dummy" in GitServiceFactory.get_available_services()

        # Create instance
        service = GitServiceFactory.create("dummy", access_token="test_token")
        assert isinstance(service, DummyGitService)
        assert service.access_token == "test_token"

    def test_register_service_overwrites_existing(self):
        """Test that registering a service overwrites existing one."""
        # Register dummy service with same name as existing
        GitServiceFactory.register_service("mock", DummyGitService)

        # Create service - should be DummyGitService, not MockGitService
        service = GitServiceFactory.create("mock")
        assert isinstance(service, DummyGitService)

    def test_get_available_services(self):
        """Test getting list of available services."""
        services = GitServiceFactory.get_available_services()

        assert isinstance(services, list)
        assert "github" in services
        assert "forgejo" in services
        assert "mock" in services

    def test_get_available_services_after_registration(self):
        """Test that available services list updates after registration."""
        # Initial services
        initial_services = GitServiceFactory.get_available_services()
        assert "dummy" not in initial_services

        # Register new service
        GitServiceFactory.register_service("dummy", DummyGitService)

        # Check updated list
        updated_services = GitServiceFactory.get_available_services()
        assert "dummy" in updated_services

    def test_create_github_without_token(self, monkeypatch):
        """Test creating GitHub service without access token."""
        # Mock settings to not have GitHub token
        monkeypatch.setattr("doc_ai_helper_backend.services.git.factory.settings.github_token", None)
        
        service = GitServiceFactory.create("github")
        assert isinstance(service, GitHubService)
        assert service.access_token is None

    def test_create_forgejo_without_base_url_raises_exception(self, monkeypatch):
        """Test that creating Forgejo without base URL raises exception."""
        # Mock settings to not have Forgejo base URL
        monkeypatch.setattr("doc_ai_helper_backend.services.git.factory.settings.forgejo_base_url", None)
        
        with pytest.raises(GitServiceException) as exc_info:
            GitServiceFactory.create("forgejo")

        assert "Forgejo base URL is required" in str(exc_info.value)

    def test_factory_normalizes_case(self):
        """Test that factory normalizes service type to lowercase."""
        # Test lowercase
        service1 = GitServiceFactory.create("github")
        assert isinstance(service1, GitHubService)

        # Test uppercase - should work due to normalization
        service2 = GitServiceFactory.create("GITHUB")
        assert isinstance(service2, GitHubService)

        # Test mixed case - should work due to normalization
        service3 = GitServiceFactory.create("GitHub")
        assert isinstance(service3, GitHubService)

    def test_create_service_with_none_token(self):
        """Test creating service with explicitly None token."""
        service = GitServiceFactory.create("mock", access_token=None)
        assert isinstance(service, MockGitService)
        assert service.access_token is None

    def test_create_service_with_empty_token(self):
        """Test creating service with empty string token."""
        service = GitServiceFactory.create("mock", access_token="")
        assert isinstance(service, MockGitService)
        assert service.access_token == ""

    def test_create_multiple_instances_are_independent(self):
        """Test that multiple service instances are independent."""
        service1 = GitServiceFactory.create("mock", access_token="token1")
        service2 = GitServiceFactory.create("mock", access_token="token2")

        assert service1.access_token == "token1"
        assert service2.access_token == "token2"
        assert service1 is not service2  # Different instances

    def test_invalid_service_type_error_message(self):
        """Test that invalid service type gives helpful error message."""
        with pytest.raises(GitServiceException) as exc_info:
            GitServiceFactory.create("gitlab")  # Not registered

        error_message = str(exc_info.value)
        assert "Unsupported Git service: gitlab" in error_message

    @patch("doc_ai_helper_backend.services.git.factory.settings")
    def test_create_forgejo_service_with_basic_auth(self, mock_settings):
        """Test creating Forgejo service with basic auth."""
        mock_settings.forgejo_base_url = "https://git.example.com"
        mock_settings.forgejo_token = None
        mock_settings.forgejo_username = "testuser"
        mock_settings.forgejo_password = "testpass"

        service = GitServiceFactory.create(
            "forgejo", base_url="https://git.example.com"
        )
        assert isinstance(service, ForgejoService)
        assert service.username == "testuser"
        assert service.password == "testpass"

    def test_create_with_config(self):
        """Test creating service with config."""
        config = {"access_token": "test_token"}
        service = GitServiceFactory.create_with_config("github", config)

        assert isinstance(service, GitHubService)
        assert service.access_token == "test_token"

    def test_create_with_config_forgejo(self):
        """Test creating Forgejo service with config."""
        config = {"access_token": "test_token", "base_url": "https://git.example.com"}
        service = GitServiceFactory.create_with_config("forgejo", config)

        assert isinstance(service, ForgejoService)
        assert service.access_token == "test_token"
        assert service.base_url == "https://git.example.com"

    def test_test_service_connection_success(self):
        """Test service connection test success."""
        result = GitServiceFactory.test_service_connection("mock", access_token="token")

        assert result["service"] == "mock"
        assert result["status"] == "created"
        assert "auth_methods" in result
        assert "configured" in result

    def test_test_service_connection_failure(self):
        """Test service connection test failure."""
        result = GitServiceFactory.test_service_connection("unsupported")

        assert result["service"] == "unsupported"
        assert result["status"] == "error"
        assert "error" in result

    @patch("doc_ai_helper_backend.services.git.factory.settings")
    def test_get_access_token_from_settings_github(self, mock_settings):
        """Test getting GitHub token from settings."""
        mock_settings.github_token = "github_token"

        token = GitServiceFactory._get_access_token_from_settings("github")
        assert token == "github_token"

    @patch("doc_ai_helper_backend.services.git.factory.settings")
    def test_get_access_token_from_settings_forgejo(self, mock_settings):
        """Test getting Forgejo token from settings."""
        mock_settings.forgejo_token = "forgejo_token"

        token = GitServiceFactory._get_access_token_from_settings("forgejo")
        assert token == "forgejo_token"

    def test_get_access_token_from_settings_unknown(self):
        """Test getting token for unknown service returns None."""
        token = GitServiceFactory._get_access_token_from_settings("unknown")
        assert token is None

    def test_is_service_supported(self):
        """Test checking if service is supported."""
        assert GitServiceFactory.is_service_supported("github") is True
        assert GitServiceFactory.is_service_supported("forgejo") is True
        assert GitServiceFactory.is_service_supported("mock") is True
        assert GitServiceFactory.is_service_supported("unsupported") is False
