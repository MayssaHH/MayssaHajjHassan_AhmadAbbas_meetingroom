"""
Shared dependencies for the Reviews service.

This module defines:

* A database session provider ``get_db``.
* A ``CurrentUser`` model populated from JWT tokens.
* Helper dependencies for authentication and moderation checks.
"""

from __future__ import annotations

from typing import Generator

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from common.auth import decode_access_token
from common.config import get_settings
from common.rbac import (
    ROLE_ADMIN,
    ROLE_MODERATOR,
    ROLE_AUDITOR,
    ROLE_REGULAR,
    ROLE_FACILITY_MANAGER,
    has_role,
)
from common.exceptions import UnauthorizedError, ForbiddenError
from common.rate_limiter import check_rate_limit

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

    Raises :class:`fastapi.HTTPException` if the token is invalid or
    contains insufficient information.
    """
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except Exception:  # noqa: BLE001
        raise UnauthorizedError("Invalid authentication token.")

    user_id = payload.get("sub")
    username = payload.get("username", "")
    role = payload.get("role")

    if user_id is None or role is None:
        raise UnauthorizedError("Token missing required claims.")

    return CurrentUser(id=int(user_id), username=str(username), role=str(role))


def require_authenticated(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    Ensure that the caller is authenticated.

    This helper mainly exists for readability in router signatures.
    """
    return user


def require_moderator_or_admin(
    user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """
    Ensure that the caller has either the ``admin`` or ``moderator`` role.

    This dependency can be injected into endpoints that are restricted
    to review moderation personnel.
    """
    if not has_role(user.role, [ROLE_ADMIN, ROLE_MODERATOR]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to moderate reviews.",
        )
    return user


def require_admin_only(
    user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """
    Ensure that the caller has the ``admin`` role only.

    This dependency is for admin-only operations like deleting/restoring reviews
    and viewing all reviews in the system.
    """
    if not has_role(user.role, [ROLE_ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires admin privileges.",
        )
    return user


def require_read_access(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    Allow any authenticated user with read privileges (including auditor).
    """
    if not has_role(
        user.role,
        [ROLE_ADMIN, ROLE_MODERATOR, ROLE_AUDITOR, ROLE_REGULAR, ROLE_FACILITY_MANAGER],
    ):
        raise ForbiddenError("You do not have permission to view reviews.")
    return user


def allow_owner_or_admin_or_moderator(
    review_user_id: int,
    current: CurrentUser,
) -> None:
    """
    Helper to assert ownership or elevated roles.
    """
    if current.id == review_user_id:
        return
    if has_role(current.role, [ROLE_ADMIN, ROLE_MODERATOR]):
        return
    raise ForbiddenError("You are not allowed to modify this review.")


def rate_limit_by_user(endpoint: str):
    def _dep(current_user: CurrentUser = Depends(get_current_user)):
        check_rate_limit(f"{endpoint}:{current_user.id}")
    return _dep
