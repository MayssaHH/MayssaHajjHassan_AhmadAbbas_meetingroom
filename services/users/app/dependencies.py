"""
Shared dependency functions for the Users service.

In FastAPI, dependencies are commonly used for:

* Database session management.
* Authentication (extracting the current user from a JWT).
* Authorization (enforcing role-based access control).

In this initial commit, the functions are provided as stubs and will be
wired to real implementations in later commits.
"""

from typing import Any, Dict


def get_db() -> Any:
    """
    Placeholder for a database session dependency.

    Returns
    -------
    Any
        A database session object once implemented.

    Notes
    -----
    The concrete implementation will:

    * Use the database engine and session factory defined in the ``db`` package.
    * Yield a session per request.
    * Ensure proper closing/rollback of the session after the request.
    """
    raise NotImplementedError("get_db is not implemented yet.")


def get_current_user() -> Dict[str, Any]:
    """
    Placeholder for retrieving the current authenticated user.

    Returns
    -------
    dict
        A dictionary representing the authenticated user, typically containing
        the user ID, username, and role.

    Notes
    -----
    In later commits this dependency will:

    * Read the ``Authorization`` header from the HTTP request.
    * Validate the JWT using :mod:`common.auth`.
    * Fetch any additional user information from the Users database if needed.
    """
    raise NotImplementedError("get_current_user is not implemented yet.")
