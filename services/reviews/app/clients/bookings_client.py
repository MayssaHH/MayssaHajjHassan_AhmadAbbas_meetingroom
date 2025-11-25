"""
Thin Bookings service client for the Reviews service.

This client can optionally be used to ensure that a user has previously
booked a room before submitting a review. For Commit 6 it simply
returns ``True`` without performing any external call.
"""

from __future__ import annotations


def user_has_booking_for_room(user_id: int, room_id: int) -> bool:
    """
    Return whether the given user has (or had) a booking for the room.

    In Commit 6 this is a stub that always returns ``True``. If you
    later decide to enforce "only reviewers with bookings", this
    function can be extended to call the Bookings service.
    """
    # TODO: Replace stub with real HTTP call to the Bookings service.
    return True
