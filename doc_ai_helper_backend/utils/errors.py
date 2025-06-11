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
