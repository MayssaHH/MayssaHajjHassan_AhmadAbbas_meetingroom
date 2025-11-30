"""
Entry point for the Rooms FastAPI application.

The application defined here is used both by the development server
(``uvicorn``) and by the pytest-based test suite.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from common.exceptions import AppError
from .routers import rooms_routes

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Smart Meeting Room - Rooms Service",
    version="0.1.0",
)


# Exception handlers
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """
    Handle custom application errors.

    Uses exc.http_status as HTTP status and exc.to_dict() for response.
    """
    return JSONResponse(
        status_code=exc.http_status,
        content=exc.to_dict(),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle request validation errors.

    Returns 400 with VALIDATION_ERROR code and validation details.
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Request validation failed.",
            "details": {"errors": exc.errors()},
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTPException.

    Maps common status codes to error codes:
    - 401 → UNAUTHORIZED
    - 403 → FORBIDDEN
    - 404 → NOT_FOUND
    - others → HTTP_ERROR
    """
    error_code_map = {
        status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
        status.HTTP_403_FORBIDDEN: "FORBIDDEN",
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
    }

    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": error_code,
            "message": message,
            "details": {},
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions.

    Logs the exception and returns 500 with INTERNAL_ERROR.
    """
    logger.exception(
        "Unhandled exception: %s",
        exc,
        extra={"path": request.url.path, "method": request.method},
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "Unexpected server error",
            "details": {},
        },
    )


# API v1 router
api_v1 = APIRouter(prefix="/api/v1")

api_v1.include_router(rooms_routes.router, prefix="/rooms", tags=["rooms"])

app.include_router(api_v1)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """
    Lightweight health-check endpoint.

    Returns a simple JSON object indicating that the service is running.
    """
    return {"status": "ok"}
