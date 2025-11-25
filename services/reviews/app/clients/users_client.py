"""
Thin Users service client for the Reviews service.

For Commit 6 this module only exposes a stub implementation that always
considers the user as valid. In later commits it will be extended to
perform real HTTP requests using :mod:`common.http_client`.
"""

from __future__ import annotations


def ensure_user_exists(user_id: int) -> bool:
    """
    Indicate whether the given user exists.

    Returns ``True`` in Commit 6. This keeps the API stable while
    allowing validation to be tightened later without breaking callers.
    """
    # TODO: Replace stub with real HTTP call to the Users service.
    return True
