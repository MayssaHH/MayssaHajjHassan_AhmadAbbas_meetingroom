"""
Shared dependencies for the Bookings service.

This module wires:

* Database session management.
* Authentication of the current user via JWT.
* Simple role-based access helpers.
"""

from typing import Callable, List

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from common.auth import verify_access_token
from common.rbac import (
    is_role_allowed,
    ROLE_ADMIN,
    ROLE_FACILITY_MANAGER,
    ROLE_AUDITOR,
    ROLE_SERVICE_ACCOUNT,
)
from common.exceptions import UnauthorizedError, ForbiddenError
from common.rate_limiter import check_rate_limit
from db.init_db import get_db as _get_db


security_scheme = HTTPBearer()


class CurrentUser(BaseModel):
    """
    Lightweight representation of the authenticated user used by the Bookings service.
    """

    id: int
    role: str


def get_db() -> Session:
    """
    Database dependency for the Bookings service.

    Returns
    -------
    Session
        A SQLAlchemy session.
    """
    # _get_db is a generator that yields a session; we take the first yielded value.
    return next(_get_db())  # type: ignore[stop-iteration]


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> CurrentUser:
    """
    Decode the JWT token and return the current user.

    The token is expected to contain at least:

    * ``sub``: user identifier
    * ``role``: user's role

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
    role = payload.get("role")

    if user_id is None or role is None:
        raise UnauthorizedError("Token missing required claims.")

    return CurrentUser(id=int(user_id), role=str(role))


def require_roles(allowed_roles: List[str]) -> Callable[[CurrentUser], CurrentUser]:
    """
    Build a dependency that checks the current user's role.

    Parameters
    ----------
    allowed_roles:
        Roles that are allowed to access the protected endpoint.

    Returns
    -------
    Callable
        A dependency that returns the current user if authorized, otherwise
        raises :class:`fastapi.HTTPException`.
    """

    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not is_role_allowed(current_user.role, allowed_roles):
            raise ForbiddenError("Insufficient permissions.")
        return current_user

    return dependency


# Convenience aliases for later use
ADMIN_ROLES = [ROLE_ADMIN]
ADMIN_OR_FM_OR_AUDITOR_ROLES = [ROLE_ADMIN, ROLE_FACILITY_MANAGER, ROLE_AUDITOR]
ADMIN_FM_AUDITOR_SERVICE = [ROLE_ADMIN, ROLE_FACILITY_MANAGER, ROLE_AUDITOR, ROLE_SERVICE_ACCOUNT]


def rate_limit_by_user(endpoint: str):
    def _dep(current_user: CurrentUser = Depends(get_current_user)):
        check_rate_limit(f"{endpoint}:{current_user.id}")
    return _dep
