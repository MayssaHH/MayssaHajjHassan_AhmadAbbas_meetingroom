"""
Data-access helpers for the ``rooms`` table.

All direct SQLAlchemy interaction for the Rooms service lives here so
that higher layers (service and routers) remain focused on business
logic and HTTP concerns.
"""

from __future__ import annotations

from typing import List, Optional
from sqlalchemy import func, and_

from sqlalchemy.orm import Session

from db.schema import Room


def get_room_by_id(db: Session, room_id: int) -> Optional[Room]:
    """
    Retrieve a single room by its primary key.
    """
    return db.query(Room).filter(Room.id == room_id).first()


def get_room_by_name(db: Session, name: str) -> Optional[Room]:
    """
    Retrieve a room by its unique name (case-insensitive).
    """
    return (
        db.query(Room)
        .filter(func.lower(Room.name) == func.lower(name))
        .first()
    )


def list_rooms(
    db: Session,
    *,
    min_capacity: Optional[int] = None,
    location: Optional[str] = None,
    equipment: Optional[str] = None,
    equipment_list: Optional[List[str]] = None,
    offset: int = 0,
    limit: Optional[int] = None,
) -> List[Room]:
    """
    Return rooms matching the provided filters.

    Parameters
    ----------
    db:
        Open database session.
    min_capacity:
        If provided, only rooms with capacity greater than or equal to
        this value are returned.
    location:
        If provided, only rooms with the exact location string are
        returned.
    equipment:
        If provided, only rooms whose ``equipment`` text contains this
        token are returned (case-insensitive ``LIKE`` filter).
    """
    query = db.query(Room)

    if min_capacity is not None:
        query = query.filter(Room.capacity >= min_capacity)

    if location is not None:
        query = query.filter(func.lower(Room.location) == func.lower(location))

    if equipment is not None:
        pattern = f"%{equipment}%"
        query = query.filter(Room.equipment.ilike(pattern))

    if equipment_list:
        for item in equipment_list:
            pattern = f"%{item}%"
            query = query.filter(Room.equipment.ilike(pattern))

    query = query.order_by(Room.id.asc())
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    return query.all()


def create_room(
    db: Session,
    *,
    name: str,
    location: str,
    capacity: int,
    equipment_csv: str,
    status: str = "active",
) -> Room:
    """
    Insert a new room into the database.
    """
    room = Room(
        name=name,
        location=location,
        capacity=capacity,
        equipment=equipment_csv,
        status=status,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


def save_room(db: Session, room: Room) -> Room:
    """
    Persist modifications made to an existing room.
    """
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


def delete_room(db: Session, room: Room) -> None:
    """
    Delete a room from the database.
    """
    db.delete(room)
    db.commit()
