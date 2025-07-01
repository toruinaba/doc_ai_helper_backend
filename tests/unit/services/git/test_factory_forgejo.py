"""
Tests for Git service factory with Forgejo support.
"""

import pytest
from unittest.mock import patch, MagicMock

from doc_ai_helper_backend.core.exceptions import GitServiceException
from doc_ai_helper_backend.services.git.factory import GitServiceFactory
from doc_ai_helper_backend.services.git.forgejo_service import ForgejoService
from doc_ai_helper_backend.services.git.github_service import GitHubService
from doc_ai_helper_backend.services.git.mock_service import MockGitService


class TestGitServiceFactoryForgejo:
    """Test cases for GitServiceFactory with Forgejo support."""

    def test_get_available_services(self):
        """Test getting available services includes Forgejo."""
        services = GitServiceFactory.get_available_services()
        assert "github" in services
        assert "forgejo" in services
        assert "mock" in services

    def test_create_github_service(self):
        """Test creating GitHub service."""
        service = GitServiceFactory.create("github", access_token="token")
        assert isinstance(service, GitHubService)
        assert service.access_token == "token"

    def test_create_mock_service(self):
        """Test creating Mock service."""
        service = GitServiceFactory.create("mock", access_token="token")
        assert isinstance(service, MockGitService)
        assert service.access_token == "token"

    @patch("doc_ai_helper_backend.services.git.factory.settings")
    def test_create_forgejo_service_with_token(self, mock_settings):
        """Test creating Forgejo service with token."""
        mock_settings.forgejo_base_url = "https://git.example.com"
        mock_settings.forgejo_token = "test_token"
        mock_settings.forgejo_username = None
        mock_settings.forgejo_password = None

        service = GitServiceFactory.create(
            "forgejo", access_token="custom_token", base_url="https://git.example.com"
        )
        assert isinstance(service, ForgejoService)
        assert service.access_token == "custom_token"
        assert service.base_url == "https://git.example.com"

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

    @patch("doc_ai_helper_backend.services.git.factory.settings")
    def test_create_forgejo_service_without_base_url(self, mock_settings):
        """Test creating Forgejo service without base URL raises exception."""
        mock_settings.forgejo_base_url = None
        mock_settings.forgejo_token = "token"

        with pytest.raises(GitServiceException) as exc_info:
            GitServiceFactory.create("forgejo")

        assert "Forgejo base URL is required" in str(exc_info.value)

    def test_create_forgejo_service_with_custom_base_url(self):
        """Test creating Forgejo service with custom base URL."""
        service = GitServiceFactory.create(
            "forgejo", base_url="https://custom.git.com", access_token="token"
        )
        assert isinstance(service, ForgejoService)
        assert service.base_url == "https://custom.git.com"
        assert service.access_token == "token"

    def test_create_unsupported_service(self):
        """Test creating unsupported service raises exception."""
        with pytest.raises(GitServiceException) as exc_info:
            GitServiceFactory.create("unsupported")

        assert "Unsupported Git service: unsupported" in str(exc_info.value)

    def test_create_with_config(self):
        """Test creating service with config."""
        # Test create_with_config method
        config = {"access_token": "test_token"}
        service = GitServiceFactory.create_with_config("github", config)

        assert isinstance(service, GitHubService)
        assert service.access_token == "test_token"

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

    def test_register_service(self):
        """Test registering a new service."""

        class CustomService(GitHubService):
            pass

        original_services = GitServiceFactory._services.copy()

        try:
            GitServiceFactory.register_service("custom", CustomService)
            assert "custom" in GitServiceFactory._services
            assert GitServiceFactory._services["custom"] == CustomService
        finally:
            # Restore original services
            GitServiceFactory._services = original_services
