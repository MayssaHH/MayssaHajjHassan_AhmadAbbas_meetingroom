"""
Service layer for the Users service.

This module contains the core business logic for user management, separate
from web and database details. It orchestrates between the API layer and
the repository layer.
"""

from typing import List
import re
from collections import defaultdict

from sqlalchemy.orm import Session

from common.auth import get_password_hash, verify_password, create_access_token
from common.rbac import (
    ROLE_ADMIN,
    ROLE_REGULAR,
    ROLE_FACILITY_MANAGER,
    ROLE_MODERATOR,
    ROLE_AUDITOR,
    ROLE_SERVICE_ACCOUNT,
)
from common.exceptions import BadRequestError, UnauthorizedError, ForbiddenError
from db.schema import User
from services.users.app.repository import user_repository

ALLOWED_ROLES = {
    ROLE_ADMIN,
    ROLE_REGULAR,
    ROLE_FACILITY_MANAGER,
    ROLE_MODERATOR,
    ROLE_AUDITOR,
    ROLE_SERVICE_ACCOUNT,
}

ROLE_ALIASES = {
    "facility": ROLE_FACILITY_MANAGER,
}

_failed_attempts: defaultdict[str, int] = defaultdict(int)
_MAX_ATTEMPTS = 5


def normalize_role(role: str) -> str:
    """
    Validate and normalize an incoming role string.
    """
    normalized = ROLE_ALIASES.get(role, role)
    if normalized not in ALLOWED_ROLES:
        raise ValueError(
            "Invalid role. Allowed roles are: admin, regular, facility, moderator, auditor, service_account."
        )
    return normalized


def validate_password_strength(password: str) -> None:
    """
    Enforce a minimal password policy.
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        raise ValueError("Password must contain letters and digits.")


def register_user(
    db: Session,
    *,
    name: str,
    username: str,
    email: str,
    password: str,
    role: str = "regular",
) -> User:
    """
    Register a new user.

    Parameters
    ----------
    db:
        Database session.
    name:
        Full display name for the account.
    username:
        Desired username.
    email:
        Email address.
    password:
        Plaintext password.
    role:
        Initial role for the user (defaults to ``"regular"``).

    Returns
    -------
    User
        The newly created user.

    Raises
    ------
    BadRequestError
        If the username or email is already taken, or if password validation fails.
    """
    try:
        validate_password_strength(password)
    except ValueError as e:
        raise BadRequestError(str(e), error_code="INVALID_PASSWORD") from e
    
    try:
        normalized_role = normalize_role(role)
    except ValueError as e:
        raise BadRequestError(str(e), error_code="INVALID_ROLE") from e

    if user_repository.get_user_by_username(db, username=username):
        raise BadRequestError("Username is already taken.", error_code="USER_ALREADY_EXISTS")
    if user_repository.get_user_by_email(db, email=email):
        raise BadRequestError("Email is already in use.", error_code="USER_ALREADY_EXISTS")

    hashed_password = get_password_hash(password)
    user = user_repository.create_user(
        db,
        name=name,
        username=username,
        email=email,
        password_hash=hashed_password,
        role=normalized_role,
    )
    return user


def authenticate_user(db: Session, *, username: str, password: str) -> User:
    """
    Authenticate a user given a username and plaintext password.

    Parameters
    ----------
    db:
        Database session.
    username:
        Username provided by the client.
    password:
        Plaintext password provided by the client.

    Returns
    -------
    User
        The authenticated user.

    Raises
    ------
    UnauthorizedError
        If the credentials are invalid, user not found, or account is locked.
    """
    normalized_username = username.lower()
    if _failed_attempts[normalized_username] >= _MAX_ATTEMPTS:
        raise UnauthorizedError("Too many failed attempts.", error_code="ACCOUNT_LOCKED")

    user = user_repository.get_user_by_username(db, username=username)
    if user is None:
        _failed_attempts[normalized_username] += 1
        raise UnauthorizedError("Invalid username or password.", error_code="INVALID_CREDENTIALS")

    if not verify_password(password, user.password_hash):
        _failed_attempts[normalized_username] += 1
        raise UnauthorizedError("Invalid username or password.", error_code="INVALID_CREDENTIALS")

    _failed_attempts[normalized_username] = 0
    return user


def create_user_access_token(user: User) -> str:
    """
    Create a JWT access token for the given user.

    Parameters
    ----------
    user:
        The authenticated user.

    Returns
    -------
    str
        Encoded JWT token.
    """
    return create_access_token(subject=str(user.id), role=user.role)


def list_users(db: Session) -> List[User]:
    """
    List all users for administrative or auditing purposes.
    """
    return user_repository.list_all_users(db)


def change_password(db: Session, user: User, new_password: str) -> User:
    """
    Update the password for the given user.
    """
    validate_password_strength(new_password)
    user.password_hash = get_password_hash(new_password)
    return user_repository.save_user(db, user)
