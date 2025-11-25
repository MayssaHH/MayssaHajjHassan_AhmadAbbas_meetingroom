"""
Repository layer for the Users service.

This module encapsulates all direct database interactions involving the
``users`` table. It decouples persistence concerns from business logic.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from db.schema import User


def create_user(
    db_session: Session,
    *,
    name: str,
    username: str,
    email: str,
    password_hash: str,
    role: str,
) -> User:
    """
    Persist a new user record in the database.

    Parameters
    ----------
    db_session:
        An active database session.
    name:
        Full display name of the new user.
    username:
        The unique username of the new user.
    email:
        The unique email address of the new user.
    password_hash:
        The already-hashed password for the new user.
    role:
        Initial role assigned to the user.

    Returns
    -------
    User
        The newly created :class:`User` instance.
    """
    user = User(
        name=name,
        username=username,
        email=email,
        password_hash=password_hash,
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def get_user_by_username(db_session: Session, username: str) -> Optional[User]:
    """
    Retrieve a user by their unique username.

    Parameters
    ----------
    db_session:
        An active database session.
    username:
        The username to search for.

    Returns
    -------
    User or None
        The user if found, otherwise ``None``.
    """
    return db_session.query(User).filter(User.username == username).first()


def get_user_by_email(db_session: Session, email: str) -> Optional[User]:
    """
    Retrieve a user by their unique email address.
    """
    return db_session.query(User).filter(User.email == email).first()


def get_user_by_id(db_session: Session, user_id: int) -> Optional[User]:
    """
    Retrieve a user by primary key.
    """
    return db_session.get(User, user_id)


def list_all_users(db_session: Session) -> List[User]:
    """
    Return all users stored in the database.
    """
    return db_session.query(User).order_by(User.id).all()


def delete_user(db_session: Session, user: User) -> None:
    """
    Delete a user from the database.
    """
    db_session.delete(user)
    db_session.commit()


def save_user(db_session: Session, user: User) -> User:
    """
    Persist pending changes to a user and refresh the instance.

    Parameters
    ----------
    db_session:
        An active database session.
    user:
        The :class:`User` instance with modified fields.

    Returns
    -------
    User
        The updated and refreshed instance.
    """
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
