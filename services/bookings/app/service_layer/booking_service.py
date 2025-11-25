"""
Service layer for the Bookings service.

This module implements the core booking rules:

* Users can create, update, and cancel their own bookings.
* The system prevents overlapping bookings for the same room.
* Administrators can override conflicts by force-cancelling existing bookings.

The logic here is independent from FastAPI and can be tested in isolation.
"""

from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from db.schema import Booking, Room, User
from services.bookings.app.repository import booking_repository


class BookingConflictError(Exception):
    """
    Raised when a new or updated booking conflicts with existing ones
    and the caller did not request an administrative override.
    """


class BookingPermissionError(Exception):
    """
    Raised when a user attempts to modify a booking they do not own and
    without sufficient administrative privileges.
    """


def _validate_time_range(start_time: datetime, end_time: datetime) -> None:
    """
    Validate that the time interval is well-formed.
    """
    if start_time >= end_time:
        raise ValueError("start_time must be strictly before end_time.")


def create_booking(
    db: Session,
    *,
    user_id: int,
    role: str,
    room_id: int,
    start_time: datetime,
    end_time: datetime,
    force_override: bool = False,
) -> Booking:
    """
    Create a new booking, optionally with administrative override.

    Parameters
    ----------
    db:
        Database session.
    user_id:
        Identifier of the user who is making the booking (or on whose behalf
        the booking is made).
    role:
        Role of the caller (e.g., ``'regular'``, ``'admin'``).
    room_id:
        Identifier of the room to book.
    start_time:
        Start of the booking interval.
    end_time:
        End of the booking interval.
    force_override:
        When ``True``, conflicting bookings will be force-cancelled before
        creating the new booking. This flag is reserved for administrative
        roles and is expected to be gated at the API layer.

    Raises
    ------
    ValueError
        If the time range is invalid.
    BookingConflictError
        If a conflict exists and ``force_override`` is False.
    """
    _validate_time_range(start_time, end_time)
    _ensure_user_exists(db, user_id)
    _ensure_room_exists(db, room_id)

    conflicts = booking_repository.find_conflicting_bookings(
        db,
        room_id=room_id,
        start_time=start_time,
        end_time=end_time,
    )

    if conflicts and not force_override:
        raise BookingConflictError(
            "The room is already booked in the requested time range."
        )

    if conflicts and force_override:
        # Administrative override: mark conflicting bookings as cancelled.
        for c in conflicts:
            c.status = "cancelled"
            db.add(c)
        db.commit()

    booking = booking_repository.create_booking(
        db,
        user_id=user_id,
        room_id=room_id,
        start_time=start_time,
        end_time=end_time,
        status="confirmed",
    )
    return booking


def list_all_bookings(db: Session) -> List[Booking]:
    """
    List all bookings in the system.

    This is typically used by administrative or auditing roles.
    """
    return booking_repository.list_all_bookings(db)


def list_bookings_for_user(db: Session, user_id: int) -> List[Booking]:
    """
    List all bookings that belong to a specific user.
    """
    return booking_repository.list_user_bookings(db, user_id=user_id)


def update_booking_time(
    db: Session,
    *,
    booking_id: int,
    caller_user_id: int,
    caller_role: str,
    start_time: datetime,
    end_time: datetime,
) -> Booking:
    """
    Update the time window of an existing booking.

    The booking owner may update their own booking. Administrative roles may
    update any booking.

    Raises
    ------
    BookingPermissionError
        If the caller is neither the owner nor an administrator.
    BookingConflictError
        If the new interval conflicts with other bookings.
    ValueError
        If the time range is invalid.
    """
    _validate_time_range(start_time, end_time)

    booking = booking_repository.get_booking_by_id(db, booking_id)
    if booking is None:
        raise ValueError("Booking not found.")

    is_owner = booking.user_id == caller_user_id
    is_admin_like = caller_role == "admin"

    if not (is_owner or is_admin_like):
        raise BookingPermissionError(
            "You are not allowed to modify this booking."
        )

    conflicts = booking_repository.find_conflicting_bookings(
        db,
        room_id=booking.room_id,
        start_time=start_time,
        end_time=end_time,
        exclude_booking_id=booking.id,
    )
    if conflicts:
        raise BookingConflictError(
            "The new time range conflicts with an existing booking."
        )

    booking.start_time = start_time
    booking.end_time = end_time
    return booking_repository.save_booking(db, booking)


def cancel_booking(
    db: Session,
    *,
    booking_id: int,
    caller_user_id: int,
    caller_role: str,
    force: bool = False,
) -> Booking:
    """
    Cancel a booking by setting its status to ``'cancelled'``.

    Parameters
    ----------
    force:
        If ``True``, the cancellation is treated as an administrative override.
        When ``False``, only the owner can cancel their own booking.

    Raises
    ------
    BookingPermissionError
        If the caller is neither the owner nor (for forced cancels) an admin.
    """
    booking = booking_repository.get_booking_by_id(db, booking_id)
    if booking is None:
        raise ValueError("Booking not found.")

    is_owner = booking.user_id == caller_user_id
    is_admin_like = caller_role == "admin"

    if force:
        if not is_admin_like:
            raise BookingPermissionError(
                "Only administrators may force-cancel bookings."
            )
    else:
        if not is_owner:
            raise BookingPermissionError(
                "You are not allowed to cancel this booking."
            )

    booking.status = "cancelled"
    return booking_repository.save_booking(db, booking)
def _ensure_room_exists(db: Session, room_id: int) -> None:
    """
    Ensure the referenced room exists before creating a booking.
    """
    if db.get(Room, room_id) is None:
        raise ValueError("Room does not exist.")


def _ensure_user_exists(db: Session, user_id: int) -> None:
    """
    Ensure the user making the booking exists.
    """
    if db.get(User, user_id) is None:
        raise ValueError("User does not exist.")
