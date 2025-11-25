"""
Business logic for the Rooms service.

This module sits between the FastAPI routers and the low-level
repository functions. It knows how to translate API payloads into ORM
operations and apply basic validation rules.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from ..schemas import RoomCreate, RoomRead, RoomStatusResponse, RoomUpdate
from ..repository import rooms_repository
from db.schema import Room
from ..clients import bookings_client


def _equipment_list_to_csv(equipment: Optional[list[str]]) -> str:
    """
    Convert a list of equipment items into a comma-separated string.
    """
    if not equipment:
        return ""
    return ",".join(sorted(set(equipment)))


def _equipment_csv_to_list(equipment_csv: str) -> list[str]:
    """
    Convert a comma-separated string of equipment items to a list.
    """
    if not equipment_csv:
        return []
    return [item.strip() for item in equipment_csv.split(",") if item.strip()]


def create_room(db: Session, payload: RoomCreate) -> Room:
    """
    Create a new room based on the given payload.
    """
    equipment_csv = _equipment_list_to_csv(payload.equipment)
    room = rooms_repository.create_room(
        db,
        name=payload.name,
        location=payload.location,
        capacity=payload.capacity,
        equipment_csv=equipment_csv,
        status=payload.status,
    )
    # Normalize equipment list for the API response
    room.equipment = equipment_csv  # type: ignore[attr-defined]
    return room


def update_room(db: Session, room_id: int, payload: RoomUpdate) -> Optional[Room]:
    """
    Apply partial updates to an existing room.

    Returns ``None`` if the room does not exist.
    """
    room = rooms_repository.get_room_by_id(db, room_id)
    if room is None:
        return None

    if payload.name is not None:
        room.name = payload.name
    if payload.location is not None:
        room.location = payload.location
    if payload.capacity is not None:
        room.capacity = payload.capacity
    if payload.status is not None:
        room.status = payload.status
    if payload.equipment is not None:
        room.equipment = _equipment_list_to_csv(payload.equipment)

    room = rooms_repository.save_room(db, room)
    return room


def get_room(db: Session, room_id: int) -> Optional[Room]:
    """
    Retrieve a room by id or return ``None`` if it does not exist.
    """
    return rooms_repository.get_room_by_id(db, room_id)


def list_rooms(
    db: Session,
    *,
    min_capacity: Optional[int] = None,
    location: Optional[str] = None,
    equipment: Optional[str] = None,
) -> List[Room]:
    """
    Return rooms matching the given filters.
    """
    return rooms_repository.list_rooms(
        db,
        min_capacity=min_capacity,
        location=location,
        equipment=equipment,
    )


def get_room_status(db: Session, room_id: int) -> Optional[RoomStatusResponse]:
    """
    Return a :class:`RoomStatusResponse` for the given room id.

    For Commit 4, the dynamic ``is_currently_booked`` flag is obtained
    from a stub in :mod:`app.clients.bookings_client` which always
    returns ``False``. Later commits will replace it with a real HTTP
    call to the Bookings service.
    """
    room = rooms_repository.get_room_by_id(db, room_id)
    if room is None:
        return None

    is_booked = bookings_client.is_room_currently_booked(room_id)
    return RoomStatusResponse(
        room_id=room.id,
        static_status=room.status,
        is_currently_booked=is_booked,
    )
