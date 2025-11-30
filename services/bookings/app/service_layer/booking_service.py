"""
Service layer for the Bookings service.

This module implements the core booking rules:

* Users can create, update, and cancel their own bookings.
* The system prevents overlapping bookings for the same room.
* Administrators can override conflicts by force-cancelling existing bookings.

The logic here is independent from FastAPI and can be tested in isolation.
"""

from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy.orm import Session

from db.schema import Booking, Room, User
from services.bookings.app.repository import booking_repository
from common.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError


MIN_DURATION = timedelta(minutes=5)
MAX_DURATION = timedelta(hours=24)


def _normalize_and_validate_time_range(start_time: datetime, end_time: datetime) -> tuple[datetime, datetime]:
    """
    Normalize times to UTC and validate ordering and duration.
    """
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)

    if start_time >= end_time:
        raise BadRequestError("start_time must be strictly before end_time.", error_code="INVALID_TIME_RANGE")

    duration = end_time - start_time
    if duration < MIN_DURATION:
        raise BadRequestError("Booking duration is too short.", error_code="INVALID_TIME_RANGE")
    if duration > MAX_DURATION:
        raise BadRequestError("Booking duration exceeds the allowed maximum.", error_code="INVALID_TIME_RANGE")
    return start_time, end_time


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

    Returns
    -------
    Booking
        The newly created booking.

    Raises
    ------
    BadRequestError
        If the time range is invalid (start >= end, duration too short/long).
    NotFoundError
        If the user or room does not exist, or room is not active.
    ConflictError
        If there are conflicting bookings and force_override is False.
    """
    start_time, end_time = _normalize_and_validate_time_range(start_time, end_time)
    _ensure_user_exists(db, user_id)
    _ensure_room_is_active(db, room_id)

    conflicts = booking_repository.find_conflicting_bookings(
        db,
        room_id=room_id,
        start_time=start_time,
        end_time=end_time,
    )

    if conflicts and not force_override:
        raise ConflictError("The room is already booked in the requested time range.", error_code="BOOKING_CONFLICT")

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


def list_all_bookings(db: Session, *, offset: int = 0, limit: int | None = None) -> List[Booking]:
    """
    List all bookings in the system.

    This is typically used by administrative or auditing roles.
    """
    return booking_repository.list_all_bookings(db, offset=offset, limit=limit)


def list_bookings_for_user(db: Session, user_id: int, *, offset: int = 0, limit: int | None = None) -> List[Booking]:
    """
    List all bookings that belong to a specific user.
    """
    return booking_repository.list_user_bookings(db, user_id=user_id, offset=offset, limit=limit)


def list_bookings_for_user_room(db: Session, *, user_id: int, room_id: int) -> List[Booking]:
    """
    List bookings for a specific user and room.
    """
    return [
        b
        for b in booking_repository.list_user_bookings(db, user_id=user_id)
        if b.room_id == room_id
    ]


def get_bookings_summary(db: Session) -> dict:
    """
    Return aggregated booking counts.
    """
    return booking_repository.get_bookings_summary(db)


def get_bookings_by_room(db: Session) -> List[dict]:
    """
    Return booking counts grouped by room.
    """
    return booking_repository.get_bookings_by_room(db)


def is_room_available(
    db: Session,
    *,
    room_id: int,
    start_time: datetime,
    end_time: datetime,
) -> bool:
    """
    Return True if no confirmed bookings overlap the given window.
    """
    start_time, end_time = _normalize_and_validate_time_range(start_time, end_time)
    conflicts = booking_repository.find_conflicting_bookings(
        db,
        room_id=room_id,
        start_time=start_time,
        end_time=end_time,
        exclude_booking_id=None,
    )
    return len(conflicts) == 0


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

    Returns
    -------
    Booking
        The updated booking.

    Raises
    ------
    BadRequestError
        If the time range is invalid (start >= end, duration too short/long).
    NotFoundError
        If the booking does not exist.
    ForbiddenError
        If the caller is neither the owner nor an administrator.
    ConflictError
        If the new interval conflicts with other bookings.
    """
    start_time, end_time = _normalize_and_validate_time_range(start_time, end_time)

    booking = booking_repository.get_booking_by_id(db, booking_id)
    if booking is None:
        raise NotFoundError("Booking not found.", error_code="BOOKING_NOT_FOUND")

    is_owner = booking.user_id == caller_user_id
    is_admin_like = caller_role == "admin"

    if not (is_owner or is_admin_like):
        raise ForbiddenError("You are not allowed to modify this booking.", error_code="NOT_OWNER")

    conflicts = booking_repository.find_conflicting_bookings(
        db,
        room_id=booking.room_id,
        start_time=start_time,
        end_time=end_time,
        exclude_booking_id=booking.id,
    )
    if conflicts:
        raise ConflictError("The new time range conflicts with an existing booking.", error_code="BOOKING_CONFLICT")

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

    Returns
    -------
    Booking
        The cancelled booking.

    Raises
    ------
    NotFoundError
        If the booking does not exist.
    ForbiddenError
        If the caller is neither the owner nor (for forced cancels) an admin.
    """
    booking = booking_repository.get_booking_by_id(db, booking_id)
    if booking is None:
        raise NotFoundError("Booking not found.", error_code="BOOKING_NOT_FOUND")

    is_owner = booking.user_id == caller_user_id
    is_admin_like = caller_role == "admin"

    if force:
        if not is_admin_like:
            raise ForbiddenError("Only administrators may force-cancel bookings.", error_code="NOT_OWNER")
    else:
        if not is_owner:
            raise ForbiddenError("You are not allowed to cancel this booking.", error_code="NOT_OWNER")

    if booking.status != "cancelled":
        booking.status = "cancelled"
        return booking_repository.save_booking(db, booking)
    return booking
def _ensure_room_is_active(db: Session, room_id: int) -> None:
    """
    Ensure the referenced room exists and is active before creating a booking.
    """
    room = db.get(Room, room_id)
    if room is None:
        raise NotFoundError("Room does not exist.", error_code="ROOM_NOT_FOUND")
    if getattr(room, "status", "active") != "active":
        raise BadRequestError("Room is not active.", error_code="ROOM_INACTIVE")


def _ensure_user_exists(db: Session, user_id: int) -> None:
    """
    Ensure the user making the booking exists.
    """
    if db.get(User, user_id) is None:
        raise NotFoundError("User does not exist.", error_code="USER_NOT_FOUND")
