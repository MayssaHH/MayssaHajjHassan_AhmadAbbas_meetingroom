"""
Service layer for the Users service.

This module contains the core business logic for user management, separate
from web and database details. It orchestrates between the API layer and
the repository layer.
"""

from typing import List

from sqlalchemy.orm import Session

from common.auth import get_password_hash, verify_password, create_access_token
from db.schema import User
from services.users.app.repository import user_repository


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
    ValueError
        If the username or email is already taken.
    """
    if user_repository.get_user_by_username(db, username=username):
        raise ValueError("Username is already taken.")
    if user_repository.get_user_by_email(db, email=email):
        raise ValueError("Email is already in use.")

    hashed_password = get_password_hash(password)
    user = user_repository.create_user(
        db,
        name=name,
        username=username,
        email=email,
        password_hash=hashed_password,
        role=role,
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
    ValueError
        If the credentials are invalid.
    """
    user = user_repository.get_user_by_username(db, username=username)
    if user is None:
        raise ValueError("Invalid username or password.")

    if not verify_password(password, user.password_hash):
        raise ValueError("Invalid username or password.")

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
