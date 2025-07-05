"""
Custom exceptions for the application.
"""

from typing import Any, Dict, Optional


class BaseAPIException(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        status_code: int,
        message: str,
        detail: Optional[Any] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.message = message
        self.detail = detail
        self.headers = headers
        super().__init__(self.message)


class NotFoundException(BaseAPIException):
    """Exception for resource not found errors."""

    def __init__(
        self, message: str = "Resource not found", detail: Optional[Any] = None
    ):
        super().__init__(status_code=404, message=message, detail=detail)


class GitServiceException(BaseAPIException):
    """Exception for Git service related errors."""

    def __init__(
        self, message: str = "Git service error", detail: Optional[Any] = None
    ):
        super().__init__(status_code=500, message=message, detail=detail)


class UnauthorizedException(BaseAPIException):
    """Exception for unauthorized access."""

    def __init__(
        self, message: str = "Unauthorized access", detail: Optional[Any] = None
    ):
        super().__init__(status_code=401, message=message, detail=detail)


class ServiceNotFoundError(Exception):
    """Exception raised when a requested service is not found."""

    pass


class LLMServiceException(BaseAPIException):
    """Exception for LLM service related errors."""

    def __init__(
        self, message: str = "LLM service error", detail: Optional[Any] = None
    ):
        super().__init__(status_code=500, message=message, detail=detail)


class TemplateNotFoundError(Exception):
    """Exception raised when a requested template is not found."""

    pass


class TemplateSyntaxError(Exception):
    """Exception raised when there's a syntax error in a template."""

    pass


class ForbiddenException(BaseAPIException):
    """Exception for forbidden access."""

    def __init__(self, message: str = "Forbidden access", detail: Optional[Any] = None):
        super().__init__(status_code=403, message=message, detail=detail)


class BadRequestException(BaseAPIException):
    """Exception for bad request errors."""

    def __init__(self, message: str = "Bad request", detail: Optional[Any] = None):
        super().__init__(status_code=400, message=message, detail=detail)


class RateLimitException(BaseAPIException):
    """Exception for rate limit errors."""

    def __init__(
        self, message: str = "Rate limit exceeded", detail: Optional[Any] = None
    ):
        super().__init__(status_code=429, message=message, detail=detail)


class InternalServerException(BaseAPIException):
    """Exception for internal server errors."""

    def __init__(
        self, message: str = "Internal server error", detail: Optional[Any] = None
    ):
        super().__init__(status_code=500, message=message, detail=detail)


class DocumentParsingException(BaseAPIException):
    """Exception for document parsing errors."""

    def __init__(
        self, message: str = "Document parsing error", detail: Optional[Any] = None
    ):
        super().__init__(status_code=422, message=message, detail=detail)


class ValidationException(BaseAPIException):
    """Exception for validation errors."""

    def __init__(self, message: str = "Validation error", detail: Optional[Any] = None):
        super().__init__(status_code=422, message=message, detail=detail)


# GitHub specific exceptions (integrated from MCP layer)
class GitHubException(BaseAPIException):
    """Base exception for GitHub-related errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        detail: Optional[Any] = None,
    ):
        super().__init__(status_code=status_code or 500, message=message, detail=detail)
        self.response_data = detail or {}


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
        detail: Optional[Any] = None,
    ):
        super().__init__(message, status_code, detail)


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
