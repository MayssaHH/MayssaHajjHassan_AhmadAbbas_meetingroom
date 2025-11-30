"""
common.error_handlers
=====================

Global exception handlers for FastAPI applications.

This module provides unified error handling across all services,
ensuring that all errors are returned in a consistent JSON format:
{
    "error_code": "...",
    "message": "...",
    "details": { ... }
}
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from common.exceptions import AppError, InternalServerError
from common.logging_utils import get_logger

_logger = get_logger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers for the FastAPI application.

    This function sets up handlers for:
    - AppError and its subclasses (custom application errors)
    - HTTPException (FastAPI's built-in exceptions)
    - ValidationError (Pydantic validation errors)
    - Exception (catch-all for unexpected errors)

    Parameters
    ----------
    app:
        The FastAPI application instance to register handlers on.
    """

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """
        Handle custom application errors.

        Returns errors in the unified JSON format.
        """
        _logger.warning(
            "Application error: %s - %s",
            exc.error_code,
            exc.message,
            extra={"error_code": exc.error_code, "path": request.url.path},
        )
        return JSONResponse(
            status_code=exc.http_status,
            content=exc.to_dict(),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        """
        Handle FastAPI HTTPException and convert to unified format.

        Maps common HTTP status codes to appropriate error codes.
        """
        error_code_map: dict[int, str] = {
            status.HTTP_400_BAD_REQUEST: "VALIDATION_ERROR",
            status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
            status.HTTP_403_FORBIDDEN: "FORBIDDEN",
            status.HTTP_404_NOT_FOUND: "NOT_FOUND",
            status.HTTP_409_CONFLICT: "CONFLICT",
            status.HTTP_422_UNPROCESSABLE_ENTITY: "VALIDATION_ERROR",
        }

        error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")
        message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)

        _logger.warning(
            "HTTP exception: %s - %s",
            error_code,
            message,
            extra={"error_code": error_code, "path": request.url.path},
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": error_code,
                "message": message,
                "details": {},
            },
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        """
        Handle Pydantic validation errors.

        Converts Pydantic validation errors to the unified format.
        """
        errors = exc.errors()
        details = {
            "validation_errors": [
                {
                    "field": ".".join(str(loc) for loc in err.get("loc", [])),
                    "message": err.get("msg", ""),
                    "type": err.get("type", ""),
                }
                for err in errors
            ]
        }

        _logger.warning(
            "Validation error: %s",
            str(exc),
            extra={"path": request.url.path, "errors": errors},
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": details,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Catch-all handler for unexpected exceptions.

        Logs the full error and returns a generic error response.
        """
        _logger.exception(
            "Unhandled exception: %s",
            exc,
            extra={"path": request.url.path, "method": request.method},
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=InternalServerError().to_dict(),
        )

