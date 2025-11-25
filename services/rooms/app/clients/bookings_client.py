"""
Lightweight client for interacting with the Bookings service.

For Commit 4 this module only exposes a stub implementation that always
returns ``False`` for the "currently booked" status. In later commits
it will be extended to perform real HTTP requests using
:mod:`common.http_client`.
"""

from __future__ import annotations


def is_room_currently_booked(room_id: int) -> bool:
    """
    Indicate whether the given room is currently booked.

    Parameters
    ----------
    room_id:
        Identifier of the room.

    Returns
    -------
    bool
        Always ``False`` in Commit 4. This keeps the API stable while
        allowing the dynamic behavior to be implemented later without
        breaking callers.
    """
    # TODO: Replace stub with real HTTP call to the Bookings service.
    return False
