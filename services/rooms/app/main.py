"""
Entry point for the Rooms FastAPI application.

The application defined here is used both by the development server
(``uvicorn``) and by the pytest-based test suite.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from common.exceptions import AppError, InternalServerError, UnauthorizedError, ForbiddenError, NotFoundError, BadRequestError
from common.logging_utils import get_logger, log_error
from .routers import rooms_routes

logger = get_logger(__name__)
SERVICE_NAME = "rooms"

app = FastAPI(
    title="Smart Meeting Room - Rooms Service",
    version="0.1.0",
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    log_error(logger, service_name=SERVICE_NAME, path=request.url.path, method=request.method, error_code=exc.error_code, message=exc.message)
    return JSONResponse(status_code=exc.http_status, content=exc.to_dict())


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if exc.status_code == 401:
        mapped = UnauthorizedError(message=str(exc.detail))
    elif exc.status_code == 403:
        mapped = ForbiddenError(message=str(exc.detail))
    elif exc.status_code == 404:
        mapped = NotFoundError(message=str(exc.detail))
    elif exc.status_code == 422:
        mapped = BadRequestError(message="Validation failed", details={"errors": exc.detail})
    else:
        mapped = InternalServerError()
    return await app_error_handler(request, mapped)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    mapped = BadRequestError(message="Validation failed", details={"errors": exc.errors()})
    return await app_error_handler(request, mapped)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    mapped = InternalServerError()
    return await app_error_handler(request, mapped)


app.include_router(rooms_routes.router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """
    Lightweight health-check endpoint.

    Returns a simple JSON object indicating that the service is running.
    """
    return {"status": "ok"}
