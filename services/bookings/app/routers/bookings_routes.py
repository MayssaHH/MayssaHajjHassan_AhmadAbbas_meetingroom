"""
User-facing booking endpoints.

These routes allow authenticated users to:

* Create bookings for rooms.
* View their own booking history.
* Update and cancel their own bookings.
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.init_db import get_db
from services.bookings.app import schemas
from services.bookings.app.dependencies import get_current_user, CurrentUser
from services.bookings.app.service_layer import booking_service


router = APIRouter()


@router.post(
    "/",
    response_model=schemas.BookingRead,
    status_code=status.HTTP_201_CREATED,
)
def create_booking(
    payload: schemas.BookingCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Create a new booking for the current user.

    The service ensures that the requested time range does not overlap
    with existing bookings for the same room. If a conflict is detected,
    a 409 response is returned.
    """
    try:
        booking = booking_service.create_booking(
            db,
            user_id=current_user.id,
            role=current_user.role,
            room_id=payload.room_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
            force_override=False,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except booking_service.BookingConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    return booking


@router.get(
    "/me",
    response_model=List[schemas.BookingRead],
    status_code=status.HTTP_200_OK,
)
def list_my_bookings(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Return the booking history of the current authenticated user.
    """
    bookings = booking_service.list_bookings_for_user(db, user_id=current_user.id)
    return bookings


@router.put(
    "/{booking_id}",
    response_model=schemas.BookingRead,
    status_code=status.HTTP_200_OK,
)
def update_my_booking(
    booking_id: int,
    payload: schemas.BookingUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Update the time window of one of the current user's bookings.

    The service re-validates conflicts with other bookings. If a conflict is
    detected, a 409 response is returned.
    """
    if payload.start_time is None or payload.end_time is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both start_time and end_time must be provided.",
        )

    try:
        booking = booking_service.update_booking_time(
            db,
            booking_id=booking_id,
            caller_user_id=current_user.id,
            caller_role=current_user.role,
            start_time=payload.start_time,
            end_time=payload.end_time,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except booking_service.BookingPermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except booking_service.BookingConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    return booking


@router.delete(
    "/{booking_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def cancel_my_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Cancel one of the current user's bookings.

    This is implemented as a soft delete by setting ``status='cancelled'``.
    """
    try:
        booking_service.cancel_booking(
            db,
            booking_id=booking_id,
            caller_user_id=current_user.id,
            caller_role=current_user.role,
            force=False,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except booking_service.BookingPermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    return None
