"""GitHub authentication manager."""

import os
from typing import Optional, Dict, Any
import logging

from doc_ai_helper_backend.core.exceptions import GitHubAuthError

logger = logging.getLogger(__name__)


class GitHubAuthManager:
    """Manages GitHub authentication using Personal Access Token."""

    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub authentication manager.

        Args:
            token: GitHub Personal Access Token. If None, tries to get from environment.
        """
        self._token = token or self._get_token_from_env()
        if not self._token:
            raise GitHubAuthError(
                "GitHub token not provided and GITHUB_TOKEN environment variable not set"
            )

    def _get_token_from_env(self) -> Optional[str]:
        """Get GitHub token from environment variables."""
        return os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_ACCESS_TOKEN")

    @property
    def token(self) -> str:
        """Get the GitHub token."""
        return self._token

    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for GitHub API requests.

        Returns:
            Dictionary containing Authorization header.
        """
        return {
            "Authorization": f"token {self._token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "doc-ai-helper-backend/1.0",
        }

    def validate_token(self) -> bool:
        """
        Validate if the token is properly formatted.

        Returns:
            True if token appears valid, False otherwise.
        """
        if not self._token:
            return False

        # GitHub Personal Access Tokens typically start with 'ghp_' or 'gho_'
        # Classic tokens are 40 characters long
        # Fine-grained tokens start with 'github_pat_'
        return (
            self._token.startswith(("ghp_", "gho_"))
            or self._token.startswith("github_pat_")
            or len(self._token) == 40  # Classic tokens without prefix
        )

    def mask_token(self) -> str:
        """
        Return a masked version of the token for logging.

        Returns:
            Masked token string.
        """
        if not self._token:
            return "None"

        if len(self._token) <= 8:
            return "*" * len(self._token)

        return f"{self._token[:4]}{'*' * (len(self._token) - 8)}{self._token[-4:]}"
