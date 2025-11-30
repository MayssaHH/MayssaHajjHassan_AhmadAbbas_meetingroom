"""
Users service application entrypoint.

This module exposes the FastAPI application instance for the Users service.
"""

from fastapi import FastAPI

from common.error_handlers import register_error_handlers
from services.users.app.routers import auth_routes, users_routes, admin_routes


app = FastAPI(
    title="Users Service",
    description=(
        "Microservice responsible for user registration, authentication, "
        "profile management, roles, and exposing booking history."
    ),
    version="0.1.0",
)

# Register unified error handlers
register_error_handlers(app)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """
    Simple health-check endpoint.

    Returns
    -------
    dict
        A small JSON payload indicating that the Users service is alive.
    """
    return {"status": "ok", "service": "users"}


app.include_router(auth_routes.router, prefix="/users", tags=["auth"])
app.include_router(users_routes.router, prefix="/users", tags=["users"])
app.include_router(admin_routes.router, prefix="/users", tags=["admin-users"])
