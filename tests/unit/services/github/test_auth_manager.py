"""Tests for GitHub authentication manager."""

import os
import pytest
from unittest.mock import patch, MagicMock

from doc_ai_helper_backend.services.github.auth_manager import GitHubAuthManager
from doc_ai_helper_backend.services.github.exceptions import GitHubAuthError


class TestGitHubAuthManager:
    """Test cases for GitHubAuthManager."""

    def test_init_with_token(self):
        """Test initialization with explicit token."""
        token = "ghp_1234567890abcdef1234567890abcdef12345678"
        auth_manager = GitHubAuthManager(token=token)
        assert auth_manager.token == token

    @patch.dict(os.environ, {"GITHUB_TOKEN": "test_token_from_env"})
    def test_init_with_env_var(self):
        """Test initialization with environment variable."""
        auth_manager = GitHubAuthManager()
        assert auth_manager.token == "test_token_from_env"

    @patch.dict(os.environ, {"GITHUB_ACCESS_TOKEN": "test_access_token"})
    def test_init_with_access_token_env(self):
        """Test initialization with GITHUB_ACCESS_TOKEN environment variable."""
        auth_manager = GitHubAuthManager()
        assert auth_manager.token == "test_access_token"

    @patch.dict(os.environ, {}, clear=True)
    def test_init_without_token_raises_error(self):
        """Test that initialization without token raises error."""
        with pytest.raises(GitHubAuthError, match="GitHub token not provided"):
            GitHubAuthManager()

    def test_get_auth_headers(self):
        """Test getting authentication headers."""
        token = "test_token"
        auth_manager = GitHubAuthManager(token=token)
        headers = auth_manager.get_auth_headers()

        expected_headers = {
            "Authorization": "token test_token",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "doc-ai-helper-backend/1.0",
        }
        assert headers == expected_headers

    def test_validate_token_valid_ghp(self):
        """Test token validation with valid ghp_ token."""
        token = "ghp_1234567890abcdef1234567890abcdef12345678"
        auth_manager = GitHubAuthManager(token=token)
        assert auth_manager.validate_token() is True

    def test_validate_token_valid_classic(self):
        """Test token validation with valid classic token."""
        token = "1234567890abcdef1234567890abcdef12345678"  # 40 chars
        auth_manager = GitHubAuthManager(token=token)
        assert auth_manager.validate_token() is True

    def test_validate_token_valid_fine_grained(self):
        """Test token validation with valid fine-grained token."""
        token = "github_pat_1234567890abcdef"
        auth_manager = GitHubAuthManager(token=token)
        assert auth_manager.validate_token() is True

    def test_validate_token_invalid(self):
        """Test token validation with invalid token."""
        token = "invalid_token"
        auth_manager = GitHubAuthManager(token=token)
        assert auth_manager.validate_token() is False

    def test_mask_token_short(self):
        """Test token masking for short tokens."""
        token = "short"
        auth_manager = GitHubAuthManager(token=token)
        assert auth_manager.mask_token() == "*****"

    def test_mask_token_long(self):
        """Test token masking for long tokens."""
        token = "ghp_1234567890abcdef1234567890abcdef12345678"
        auth_manager = GitHubAuthManager(token=token)
        masked = auth_manager.mask_token()
        assert masked.startswith("ghp_")
        assert masked.endswith("5678")
        assert "*" in masked

    def test_mask_token_none(self):
        """Test token masking when token is None."""
        # This test requires mocking since __init__ would raise an error
        with patch.object(
            GitHubAuthManager, "_get_token_from_env", return_value="test"
        ):
            auth_manager = GitHubAuthManager()
            auth_manager._token = None
            assert auth_manager.mask_token() == "None"
