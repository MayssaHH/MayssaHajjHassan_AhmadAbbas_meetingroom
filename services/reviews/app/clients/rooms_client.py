"""
Thin Rooms service client for the Reviews service.

For Commit 6 this module only exposes a stub implementation that always
considers the room as valid and active. In later commits it will be
extended to perform real HTTP requests using :mod:`common.http_client`.
"""

from __future__ import annotations


def ensure_room_is_active(room_id: int) -> bool:
    """
    Indicate whether the given room exists and is active.

    Returns ``True`` in Commit 6. This keeps the API stable while
    allowing validation to be tightened later without breaking callers.
    """
    # TODO: Replace stub with real HTTP call to the Rooms service.
    return True
