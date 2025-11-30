"""
Service layer for the Rooms service.

This module contains the core business logic for room management, separate
from HTTP and persistence concerns.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from db.schema import Room
from services.rooms.app.repository import rooms_repository


def create_room(
    db: Session,
    *,
    name: str,
    capacity: int,
    equipment: Optional[str],
    location: Optional[str],
    status: str = "active",
) -> Room:
    """
    Create a new room, enforcing uniqueness on the room name.
    """
    if rooms_repository.get_room_by_name(db, name=name):
        raise ValueError("Room name is already in use.")
    return rooms_repository.create_room(
        db,
        name=name,
        capacity=capacity,
        equipment=equipment,
        location=location,
        status=status,
    )


def update_room(
    db: Session,
    room: Room,
    *,
    name: Optional[str] = None,
    capacity: Optional[int] = None,
    equipment: Optional[str] = None,
    location: Optional[str] = None,
    status: Optional[str] = None,
) -> Room:
    """
    Update mutable fields of an existing room.
    """
    if name is not None and name != room.name:
        if rooms_repository.get_room_by_name(db, name=name):
            raise ValueError("Room name is already in use.")
        room.name = name

    if capacity is not None:
        room.capacity = capacity

    if equipment is not None:
        room.equipment = equipment

    if location is not None:
        room.location = location

    if status is not None:
        room.status = status

    return rooms_repository.save_room(db, room)


def list_rooms(
    db: Session,
    *,
    min_capacity: Optional[int] = None,
    location: Optional[str] = None,
    equipment_contains: Optional[str] = None,
) -> List[Room]:
    """
    List rooms using optional filters.
    """
    return rooms_repository.list_rooms(
        db,
        min_capacity=min_capacity,
        location=location,
        equipment_contains=equipment_contains,
    )
