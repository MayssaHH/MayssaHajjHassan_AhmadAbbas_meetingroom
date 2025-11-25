"""
Repository layer for the Users service.

This module will encapsulate all direct database interactions involving the
``users`` table. It decouples persistence concerns from business logic.
"""

from typing import Any, Dict, List, Optional


def create_user(db_session: Any, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Persist a new user record in the database.

    Parameters
    ----------
    db_session:
        An active database session.
    data:
        A dictionary containing all user fields to persist.

    Returns
    -------
    dict
        A representation of the newly created user.
    """
    raise NotImplementedError("create_user is not implemented yet.")


def get_user_by_username(db_session: Any, username: str) -> Optional[Dict[str, Any]]:
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
    dict or None
        The user representation if found, otherwise ``None``.
    """
    raise NotImplementedError("get_user_by_username is not implemented yet.")


def list_all_users(db_session: Any) -> List[Dict[str, Any]]:
    """
    Return all users stored in the database.

    Parameters
    ----------
    db_session:
        An active database session.

    Returns
    -------
    list of dict
        A list of user records.
    """
    raise NotImplementedError("list_all_users is not implemented yet.")
