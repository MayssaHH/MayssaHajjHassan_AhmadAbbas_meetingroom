"""
HTTP endpoints for managing rooms and querying their status.

This router is mounted under the ``/rooms`` prefix in
:mod:`app.main`.
"""

from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import schemas
from ..dependencies import CurrentUser, get_current_user, get_db, require_room_manager
from ..service_layer import rooms_service

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post(
    "",
    response_model=schemas.RoomRead,
    status_code=status.HTTP_201_CREATED,
)
def create_room(
    payload: schemas.RoomCreate,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_room_manager),
):
    """
    Create a new meeting room.

    Only users with the ``admin`` or ``facility_manager`` role are
    allowed to access this endpoint.
    """
    try:
        room = rooms_service.create_room(db, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return room


@router.get(
    "",
    response_model=List[schemas.RoomRead],
)
def list_rooms(
    min_capacity: Optional[int] = Query(
        default=None,
        description="If provided, only rooms with capacity >= this value are returned.",
    ),
    location: Optional[str] = Query(
        default=None,
        description="If provided, only rooms at this location are returned.",
    ),
    equipment: Optional[str] = Query(
        default=None,
        description="If provided, only rooms whose equipment includes this token are returned.",
    ),
    equipment_list: Optional[List[str]] = Query(
        default=None,
        description="Multiple equipment tokens that must all be present.",
    ),
    offset: int = 0,
    limit: Optional[int] = None,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    """
    List rooms with optional filters on capacity, location, and equipment.
    """
    rooms = rooms_service.list_rooms(
        db,
        min_capacity=min_capacity,
        location=location,
        equipment=equipment,
        equipment_list=equipment_list,
        offset=offset,
        limit=limit,
    )
    return rooms


@router.get(
    "/{room_id}",
    response_model=schemas.RoomRead,
)
def get_room(
    room_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    """
    Retrieve a single room by its identifier.
    """
    room = rooms_service.get_room(db, room_id)
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found.",
        )
    return room


@router.put(
    "/{room_id}",
    response_model=schemas.RoomRead,
)
def update_room(
    room_id: int,
    payload: schemas.RoomUpdate,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_room_manager),
):
    """
    Update an existing room.

    Only room managers (admins or facility managers) are allowed to
    call this endpoint.
    """
    try:
        room = rooms_service.update_room(db, room_id, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found.",
        )
    return room


@router.delete(
    "/{room_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_room_manager),
):
    """
    Delete a room.

    Only room managers (admins or facility managers) are allowed to
    call this endpoint.
    """
    room = rooms_service.get_room(db, room_id)
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found.",
        )
    from ..repository import rooms_repository

    rooms_repository.delete_room(db, room)
    return None


@router.get(
    "/{room_id}/status",
    response_model=schemas.RoomStatusResponse,
)
def get_room_status(
    room_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
):
    """
    Return the static and dynamic status of a room.

    The dynamic part (whether the room is currently booked) is a stub in
    Commit 4 and always returns ``False``.
    """
    status_obj = rooms_service.get_room_status(db, room_id, start_time=start_time, end_time=end_time)
    if status_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found.",
        )
    return status_obj
