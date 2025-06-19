"""
Error handlers for the API.
"""

import logging
from typing import Any, Dict, Union

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from doc_ai_helper_backend.core.exceptions import (
    BadRequestException,
    BaseAPIException,
    DocumentParsingException,
    ForbiddenException,
    GitServiceException,
    InternalServerException,
    LLMServiceException,
    NotFoundException,
    RateLimitException,
    UnauthorizedException,
    ValidationException,
)

logger = logging.getLogger("doc_ai_helper")


def setup_error_handlers(app: FastAPI) -> None:
    """
    Setup error handlers for the application.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Handle generic exceptions.

        Args:
            request: FastAPI request object
            exc: Exception that was raised

        Returns:
            JSONResponse with error details
        """
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal server error",
                "detail": str(exc) if str(exc) else "An unexpected error occurred",
            },
        )

    @app.exception_handler(BaseAPIException)
    async def api_exception_handler(
        request: Request, exc: BaseAPIException
    ) -> JSONResponse:
        """
        Handle base API exceptions.

        Args:
            request: FastAPI request object
            exc: BaseAPIException that was raised

        Returns:
            JSONResponse with error details
        """
        logger.error(f"API exception: {exc.message}, detail: {exc.detail}")
        response = {"message": exc.message}
        if exc.detail:
            response["detail"] = exc.detail

        return JSONResponse(
            status_code=exc.status_code, content=response, headers=exc.headers
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        """
        Handle pydantic validation errors.

        Args:
            request: FastAPI request object
            exc: ValidationError that was raised

        Returns:
            JSONResponse with error details
        """
        logger.error(f"Validation error: {exc}")
        return JSONResponse(
            status_code=422,
            content={
                "message": "Validation error",
                "detail": exc.errors(),
            },
        )  # Register specific exception handlers

    app.add_exception_handler(NotFoundException, api_exception_handler)
    app.add_exception_handler(GitServiceException, api_exception_handler)
    app.add_exception_handler(LLMServiceException, api_exception_handler)
    app.add_exception_handler(UnauthorizedException, api_exception_handler)
    app.add_exception_handler(ForbiddenException, api_exception_handler)
    app.add_exception_handler(BadRequestException, api_exception_handler)
    app.add_exception_handler(RateLimitException, api_exception_handler)
    app.add_exception_handler(InternalServerException, api_exception_handler)
    app.add_exception_handler(DocumentParsingException, api_exception_handler)
    app.add_exception_handler(ValidationException, api_exception_handler)
