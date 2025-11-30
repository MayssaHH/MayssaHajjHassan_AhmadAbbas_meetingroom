"""
Entry point for the Rooms FastAPI application.

The application defined here is used both by the development server
(``uvicorn``) and by the pytest-based test suite.
"""

from __future__ import annotations

from fastapi import FastAPI

from common.error_handlers import register_error_handlers
from .routers import rooms_routes

app = FastAPI(
    title="Smart Meeting Room - Rooms Service",
    version="0.1.0",
)

# Register unified error handlers
register_error_handlers(app)

app.include_router(rooms_routes.router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """
    Lightweight health-check endpoint.

    Returns a simple JSON object indicating that the service is running.
    """
    return {"status": "ok"}
