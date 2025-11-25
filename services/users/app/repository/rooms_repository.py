"""
Repository layer for the Rooms service.

This module encapsulates all direct database interactions involving the
``rooms`` table.
"""

from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_

from db.schema import Room


def create_room(
    db_session: Session,
    *,
    name: str,
    capacity: int,
    equipment: Optional[str],
    location: Optional[str],
    status: str = "active",
) -> Room:
    """
    Persist a new room record in the database.
    """
    room = Room(
        name=name,
        capacity=capacity,
        equipment=equipment,
        location=location,
        status=status,
    )
    db_session.add(room)
    db_session.commit()
    db_session.refresh(room)
    return room


def get_room_by_name(db_session: Session, name: str) -> Optional[Room]:
    """
    Retrieve a room by its unique name.
    """
    return db_session.query(Room).filter(Room.name == name).first()


def get_room_by_id(db_session: Session, room_id: int) -> Optional[Room]:
    """
    Retrieve a room by primary key.
    """
    return db_session.get(Room, room_id)


def list_rooms(
    db_session: Session,
    *,
    min_capacity: Optional[int] = None,
    location: Optional[str] = None,
    equipment_contains: Optional[str] = None,
) -> List[Room]:
    """
    Return rooms filtered by optional criteria.
    """
    query = db_session.query(Room)

    conditions = []
    if min_capacity is not None:
        conditions.append(Room.capacity >= min_capacity)
    if location is not None:
        conditions.append(Room.location == location)
    if equipment_contains:
        conditions.append(Room.equipment.contains(equipment_contains))

    if conditions:
        query = query.filter(and_(*conditions))

    return query.order_by(Room.id).all()


def save_room(db_session: Session, room: Room) -> Room:
    """
    Persist pending changes to a room and refresh the instance.
    """
    db_session.add(room)
    db_session.commit()
    db_session.refresh(room)
    return room


def delete_room(db_session: Session, room: Room) -> None:
    """
    Delete a room from the database.
    """
    db_session.delete(room)
    db_session.commit()
