"""
Shared dependencies for the Rooms service.

This module defines:

* A database session provider ``get_db``.
* A ``CurrentUser`` model populated from JWT tokens.
* Helper dependency ``require_room_manager`` that ensures the caller
  has either the ``admin`` or ``facility_manager`` role.
"""

from __future__ import annotations

from typing import Generator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from common.auth import verify_access_token
from common.config import get_settings
from common.rbac import ROLE_ADMIN, ROLE_FACILITY_MANAGER, has_role
from common.exceptions import UnauthorizedError, ForbiddenError

# ---------------------------------------------------------------------------
# Database session factory
# ---------------------------------------------------------------------------

settings = get_settings()

engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session bound to the main application database.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Authentication / Authorization helpers
# ---------------------------------------------------------------------------

security_scheme = HTTPBearer(auto_error=True)


class CurrentUser(BaseModel):
    """
    Minimal representation of the authenticated user used by this service.
    """

    id: int
    username: str
    role: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> CurrentUser:
    """
    Decode the JWT token and return the current user.

    Raises
    ------
    HTTPException
        If the token is invalid or missing required claims.
    """
    token = credentials.credentials

    try:
        payload = verify_access_token(token)
    except Exception:  # noqa: BLE001
        raise UnauthorizedError("Invalid authentication token.")

    user_id = payload.get("sub")
    # Our Users JWT currently sets only "sub" and "role".
    # "username" may be missing, so we default to empty string.
    username = payload.get("username", "")
    role = payload.get("role")

    if user_id is None or role is None:
        raise UnauthorizedError("Token missing required claims.")

    return CurrentUser(id=int(user_id), username=str(username), role=str(role))


def require_room_manager(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    Ensure that the caller has either the ``admin`` or
    ``facility_manager`` role.

    This dependency can be injected into endpoints that are restricted
    to room management personnel.
    """
    if not has_role(current_user.role, [ROLE_ADMIN, ROLE_FACILITY_MANAGER]):
        raise ForbiddenError("You do not have permission to manage rooms.")
    return current_user
