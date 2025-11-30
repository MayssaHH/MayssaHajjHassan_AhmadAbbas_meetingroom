"""
Bookings service application entrypoint.

This module exposes the FastAPI application instance for the Bookings service.
"""

from fastapi import FastAPI

from common.error_handlers import register_error_handlers
from services.bookings.app.routers import bookings_routes, admin_routes, analytics_routes


app = FastAPI(
    title="Bookings Service",
    description=(
        "Microservice responsible for managing room bookings, preventing "
        "conflicts, and exposing administrative overrides."
    ),
    version="0.1.0",
)

# Register unified error handlers
register_error_handlers(app)

@app.get("/health", tags=["health"])
def health_check() -> dict:
    """
    Simple health-check endpoint.
    """
    return {"status": "ok", "service": "bookings"}


app.include_router(bookings_routes.router, prefix="/bookings", tags=["bookings"])
app.include_router(admin_routes.router, prefix="/admin/bookings", tags=["admin-bookings"])
app.include_router(analytics_routes.router)
