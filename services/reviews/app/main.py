"""
Entry point for the Reviews FastAPI application.

The application defined here is used both by the development server
(``uvicorn``) and by the pytest-based test suite.
"""

from __future__ import annotations

from fastapi import FastAPI

from common.error_handlers import register_error_handlers
from .routers import reviews_routes, moderation_routes, admin_routes, analytics_routes

app = FastAPI(
    title="Smart Meeting Room - Reviews Service",
    version="0.1.0",
)

# Register unified error handlers
register_error_handlers(app)

app.include_router(reviews_routes.router)
app.include_router(moderation_routes.router)
app.include_router(admin_routes.router, prefix="/admin", tags=["admin-reviews"])
app.include_router(analytics_routes.router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """
    Lightweight health-check endpoint.

    Returns a simple JSON object indicating that the service is running.
    """
    return {"status": "ok"}
