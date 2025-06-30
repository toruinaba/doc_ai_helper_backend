"""GitHub service specific exceptions."""

from typing import Optional, Dict, Any


class GitHubException(Exception):
    """Base exception for GitHub-related errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class GitHubAuthError(GitHubException):
    """Exception raised for GitHub authentication errors."""

    def __init__(self, message: str = "GitHub authentication failed"):
        super().__init__(message, status_code=401)


class GitHubAPIError(GitHubException):
    """Exception raised for GitHub API errors."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code, response_data)


class GitHubRateLimitError(GitHubException):
    """Exception raised when GitHub API rate limit is exceeded."""

    def __init__(self, reset_time: Optional[int] = None):
        message = "GitHub API rate limit exceeded"
        if reset_time:
            message += f". Rate limit resets at {reset_time}"
        super().__init__(message, status_code=403)
        self.reset_time = reset_time


class GitHubRepositoryNotFoundError(GitHubException):
    """Exception raised when repository is not found."""

    def __init__(self, repository: str):
        super().__init__(f"Repository '{repository}' not found", status_code=404)
        self.repository = repository


class GitHubPermissionError(GitHubException):
    """Exception raised for permission-related errors."""

    def __init__(self, message: str, repository: Optional[str] = None):
        super().__init__(message, status_code=403)
        self.repository = repository
