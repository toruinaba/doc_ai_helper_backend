"""
Exception and error handling utilities.
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


class APIError(Exception):
    """Base API error."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[Any] = None,
    ):
        """Initialize API error."""
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)

    def to_http_exception(self) -> HTTPException:
        """Convert to HTTPException."""
        return HTTPException(
            status_code=self.status_code,
            detail={"message": self.message, "detail": self.detail},
        )


class NotFoundError(APIError):
    """Resource not found error."""

    def __init__(
        self, message: str = "Resource not found", detail: Optional[Any] = None
    ):
        """Initialize not found error."""
        super().__init__(message, status.HTTP_404_NOT_FOUND, detail)


class ValidationError(APIError):
    """Validation error."""

    def __init__(self, message: str = "Validation error", detail: Optional[Any] = None):
        """Initialize validation error."""
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, detail)


class AuthenticationError(APIError):
    """Authentication error."""

    def __init__(
        self, message: str = "Authentication error", detail: Optional[Any] = None
    ):
        """Initialize authentication error."""
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, detail)


class AuthorizationError(APIError):
    """Authorization error."""

    def __init__(
        self, message: str = "Authorization error", detail: Optional[Any] = None
    ):
        """Initialize authorization error."""
        super().__init__(message, status.HTTP_403_FORBIDDEN, detail)


class FunctionCallError(APIError):
    """Function call error."""

    def __init__(
        self, message: str = "Function call error", detail: Optional[Any] = None
    ):
        """Initialize function call error."""
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR, detail)


class FunctionNotFoundError(APIError):
    """Function not found error."""

    def __init__(self, function_name: str, detail: Optional[Any] = None):
        """Initialize function not found error."""
        message = f"Function '{function_name}' not found"
        super().__init__(message, status.HTTP_404_NOT_FOUND, detail)


class InvalidFunctionArgumentsError(APIError):
    """Invalid function arguments error."""

    def __init__(self, function_name: str, detail: Optional[Any] = None):
        """Initialize invalid function arguments error."""
        message = f"Invalid arguments for function '{function_name}'"
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, detail)


class FunctionExecutionError(APIError):
    """Function execution error."""

    def __init__(
        self, function_name: str, error_detail: str, detail: Optional[Any] = None
    ):
        """Initialize function execution error."""
        message = f"Error executing function '{function_name}': {error_detail}"
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR, detail)
