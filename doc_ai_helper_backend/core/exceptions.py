"""
Custom exceptions for the application.
"""

import logging
from typing import Any, Dict, Optional, Union

from fastapi import HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger("doc_ai_helper")


class ErrorDetail(BaseModel):
    """Error detail model."""

    loc: Optional[str] = None
    msg: str
    type: str


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = False
    message: str
    detail: Optional[Union[str, Dict[str, Any], ErrorDetail]] = None
    status_code: int


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

    def to_http_exception(self) -> HTTPException:
        """Convert to HTTPException."""
        return HTTPException(
            status_code=self.status_code,
            detail={"message": self.message, "detail": self.detail},
        )


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


class ServiceNotFoundError(BaseAPIException):
    """Exception raised when a requested service is not found."""

    def __init__(
        self, message: str = "Service not found", detail: Optional[Any] = None
    ):
        super().__init__(status_code=400, message=message, detail=detail)


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


# Function Calling specific exceptions
class FunctionCallError(BaseAPIException):
    """Function call error."""

    def __init__(
        self, message: str = "Function call error", detail: Optional[Any] = None
    ):
        """Initialize function call error."""
        super().__init__(status_code=500, message=message, detail=detail)


class FunctionNotFoundError(BaseAPIException):
    """Function not found error."""

    def __init__(self, function_name: str, detail: Optional[Any] = None):
        """Initialize function not found error."""
        message = f"Function '{function_name}' not found"
        super().__init__(status_code=404, message=message, detail=detail)


class InvalidFunctionArgumentsError(BaseAPIException):
    """Invalid function arguments error."""

    def __init__(self, function_name: str, detail: Optional[Any] = None):
        """Initialize invalid function arguments error."""
        message = f"Invalid arguments for function '{function_name}'"
        super().__init__(status_code=422, message=message, detail=detail)


class FunctionExecutionError(BaseAPIException):
    """Function execution error."""

    def __init__(
        self, function_name: str, error_detail: str, detail: Optional[Any] = None
    ):
        """Initialize function execution error."""
        message = f"Error executing function '{function_name}': {error_detail}"
        super().__init__(status_code=500, message=message, detail=detail)
