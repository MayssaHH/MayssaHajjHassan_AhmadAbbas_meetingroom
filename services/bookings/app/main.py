"""
Bookings service application entrypoint.

This module exposes the FastAPI application instance for the Bookings service.
"""

import logging

from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from common.exceptions import AppError
from services.bookings.app.routers import bookings_routes, admin_routes, analytics_routes

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Bookings Service",
    description=(
        "Microservice responsible for managing room bookings, preventing "
        "conflicts, and exposing administrative overrides."
    ),
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

api_v1.include_router(bookings_routes.router, prefix="/bookings", tags=["bookings"])
api_v1.include_router(admin_routes.router, prefix="/admin/bookings", tags=["admin-bookings"])
api_v1.include_router(analytics_routes.router)

app.include_router(api_v1)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """
    Simple health-check endpoint.
    """
    return {"status": "ok", "service": "bookings"}
