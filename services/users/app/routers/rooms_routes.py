"""
HTTP routes for the Rooms service.

This router exposes endpoints for:

* Creating, updating, and deleting rooms (admin / facility manager).
* Listing and retrieving room details.
* Getting a simple availability status for a room.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from common.rbac import ROLE_ADMIN, ROLE_FACILITY_MANAGER, ROLE_REGULAR, ROLE_AUDITOR, ROLE_MODERATOR
from db.schema import Room
from services.rooms.app import schemas
from services.rooms.app.dependencies import (
    get_db,
    get_current_user,
    require_roles,
)
from services.rooms.app.repository import rooms_repository
from services.rooms.app.service_layer import rooms_service


router = APIRouter()


@router.post(
    "/",
    response_model=schemas.RoomRead,
    status_code=status.HTTP_201_CREATED,
)
def create_room_endpoint(
    payload: schemas.RoomCreate,
    db: Session = Depends(get_db),
    _current = Depends(require_roles([ROLE_ADMIN, ROLE_FACILITY_MANAGER])),
):
    """
    Create a new meeting room.

    Only administrators and facility managers are allowed to create rooms.
    """
    try:
        room = rooms_service.create_room(
            db,
            name=payload.name,
            capacity=payload.capacity,
            equipment=payload.equipment,
            location=payload.location,
            status=payload.status or "active",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return room


@router.get("/", response_model=List[schemas.RoomRead])
def list_rooms_endpoint(
    min_capacity: Optional[int] = Query(
        None,
        ge=1,
        description="Filter rooms with capacity greater than or equal to this value.",
    ),
    location: Optional[str] = Query(
        None,
        description="Filter rooms that match this exact location.",
    ),
    equipment_contains: Optional[str] = Query(
        None,
        description="Filter rooms whose equipment description contains this text.",
    ),
    db: Session = Depends(get_db),
    _current = Depends(
        require_roles(
            [
                ROLE_ADMIN,
                ROLE_FACILITY_MANAGER,
                ROLE_REGULAR,
                ROLE_AUDITOR,
                ROLE_MODERATOR,
            ]
        )
    ),
):
    """
    List rooms using optional filters.

    Any authenticated user role is allowed to list rooms.
    """
    rooms = rooms_service.list_rooms(
        db,
        min_capacity=min_capacity,
        location=location,
        equipment_contains=equipment_contains,
    )
    return rooms


@router.get("/{room_id}", response_model=schemas.RoomRead)
def get_room_by_id_endpoint(
    room_id: int,
    db: Session = Depends(get_db),
    _current = Depends(get_current_user),
):
    """
    Retrieve a room by its identifier.
    """
    room = rooms_repository.get_room_by_id(db, room_id)
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found.",
        )
    return room


@router.put("/{room_id}", response_model=schemas.RoomRead)
def update_room_endpoint(
    room_id: int,
    payload: schemas.RoomUpdate,
    db: Session = Depends(get_db),
    _current = Depends(require_roles([ROLE_ADMIN, ROLE_FACILITY_MANAGER])),
):
    """
    Update an existing room.

    Only administrators and facility managers are allowed to update rooms.
    """
    room = rooms_repository.get_room_by_id(db, room_id)
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found.",
        )

    try:
        updated = rooms_service.update_room(
            db,
            room,
            name=payload.name,
            capacity=payload.capacity,
            equipment=payload.equipment,
            location=payload.location,
            status=payload.status,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return updated


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room_endpoint(
    room_id: int,
    db: Session = Depends(get_db),
    _current = Depends(require_roles([ROLE_ADMIN, ROLE_FACILITY_MANAGER])),
):
    """
    Delete a room by its identifier.

    Only administrators and facility managers are allowed to delete rooms.
    """
    room = rooms_repository.get_room_by_id(db, room_id)
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found.",
        )

    rooms_repository.delete_room(db, room)
    return None


@router.get("/{room_id}/status", response_model=schemas.RoomStatus)
def get_room_status_endpoint(
    room_id: int,
    db: Session = Depends(get_db),
    _current = Depends(get_current_user),
):
    """
    Return the current status of a room.

    For now, this returns the static ``status`` field from the ``rooms`` table.
    In a later commit, the implementation can be extended to incorporate
    booking information from the Bookings service.
    """
    room = rooms_repository.get_room_by_id(db, room_id)
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found.",
        )

    return schemas.RoomStatus(id=room.id, status=room.status)
