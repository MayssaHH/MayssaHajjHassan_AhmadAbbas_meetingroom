"""
Shared dependency functions for the Users service.

In FastAPI, dependencies are commonly used for:

* Database session management.
* Authentication (extracting the current user from a JWT).
* Authorization (enforcing role-based access control).

In this initial commit, the functions are provided as stubs and will be
wired to real implementations in later commits.
"""

from typing import Callable, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from common.auth import verify_access_token
from common.rbac import is_role_allowed
from db.init_db import get_db as _get_db
from db.schema import User

# OAuth2PasswordBearer reads the Authorization header: "Bearer <token>"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def get_db() -> Session:
    """
    Re-export the database dependency for the Users service.

    Returns
    -------
    Session
        A database session.
    """
    return next(_get_db())


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(_get_db),
) -> User:
    """
    Retrieve the current authenticated user from the JWT access token.

    Parameters
    ----------
    token:
        JWT access token extracted from the ``Authorization`` header.
    db:
        Database session injected by FastAPI.

    Returns
    -------
    User
        The corresponding :class:`db.schema.User` instance.

    Raises
    ------
    HTTPException
        If the token is invalid or the user does not exist.
    """
    try:
        payload = verify_access_token(token)
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        )

    subject = payload.get("sub")
    role = payload.get("role")

    if subject is None or role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload.",
        )

    user = db.get(User, int(subject))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )
    return user


def require_roles(allowed_roles: List[str]) -> Callable[[User], User]:
    """
    Build a dependency that ensures the current user has one of the allowed roles.

    Parameters
    ----------
    allowed_roles:
        A list of roles that are permitted to access the protected endpoint.

    Returns
    -------
    Callable
        A dependency function that returns the current user if authorized.
    """

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not is_role_allowed(current_user.role, allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return current_user

    return dependency