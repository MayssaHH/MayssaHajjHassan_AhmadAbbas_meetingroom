"""
Repository layer for the Bookings service.

This module encapsulates all direct database interactions involving the
``bookings`` table.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, or_, func, case
from sqlalchemy.orm import Session

from db.schema import Booking


def create_booking(
    db: Session,
    *,
    user_id: int,
    room_id: int,
    start_time: datetime,
    end_time: datetime,
    status: str = "confirmed",
) -> Booking:
    """
    Persist a new booking in the database.
    """
    booking = Booking(
        user_id=user_id,
        room_id=room_id,
        start_time=start_time,
        end_time=end_time,
        status=status,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def get_booking_by_id(db: Session, booking_id: int) -> Optional[Booking]:
    """
    Retrieve a booking by its primary key.
    """
    return db.get(Booking, booking_id)


def list_all_bookings(db: Session, *, offset: int = 0, limit: Optional[int] = None) -> List[Booking]:
    """
    Return all bookings stored in the database.
    """
    query = db.query(Booking).order_by(Booking.start_time)
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    return query.all()


def list_user_bookings(db: Session, user_id: int, *, offset: int = 0, limit: Optional[int] = None) -> List[Booking]:
    """
    Return all bookings belonging to a specific user.
    """
    query = (
        db.query(Booking)
        .filter(Booking.user_id == user_id)
        .order_by(Booking.start_time)
    )
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    return query.all()


def find_conflicting_bookings(
    db: Session,
    *,
    room_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_booking_id: Optional[int] = None,
) -> List[Booking]:
    """
    Return bookings that conflict with the given time range for a room.

    A conflict occurs when the time intervals overlap, excluding bookings
    that are already cancelled.
    """
    conditions = [
        Booking.room_id == room_id,
        Booking.status != "cancelled",
        or_(
            and_(Booking.start_time < end_time, Booking.end_time > start_time),
        ),
    ]
    if exclude_booking_id is not None:
        conditions.append(Booking.id != exclude_booking_id)

    return db.query(Booking).filter(*conditions).all()


def save_booking(db: Session, booking: Booking) -> Booking:
    """
    Persist changes to an existing booking and refresh it.
    """
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def delete_booking(db: Session, booking: Booking) -> None:
    """
    Permanently delete a booking record.

    Note: The main flow prefers soft cancellation via the ``status`` field.
    """
    db.delete(booking)
    db.commit()


def get_bookings_summary(db: Session) -> dict:
    """
    Return aggregate counts of bookings by status.
    """
    total = db.query(func.count(Booking.id)).scalar() or 0
    confirmed = (
        db.query(func.count(Booking.id)).filter(Booking.status == "confirmed").scalar() or 0
    )
    cancelled = (
        db.query(func.count(Booking.id)).filter(Booking.status == "cancelled").scalar() or 0
    )
    return {
        "total_bookings": total,
        "confirmed_bookings": confirmed,
        "cancelled_bookings": cancelled,
    }


def get_bookings_by_room(db: Session) -> List[dict]:
    """
    Return counts of bookings grouped by room and status.
    """
    rows = (
        db.query(
            Booking.room_id,
            func.count(Booking.id).label("total"),
            func.sum(case((Booking.status == "confirmed", 1), else_=0)).label("confirmed"),
            func.sum(case((Booking.status == "cancelled", 1), else_=0)).label("cancelled"),
        )
        .group_by(Booking.room_id)
        .all()
    )
    results: List[dict] = []
    for row in rows:
        results.append(
            {
                "room_id": row.room_id,
                "total": int(row.total or 0),
                "confirmed": int(row.confirmed or 0),
                "cancelled": int(row.cancelled or 0),
            }
        )
    return results
