"""
Administrator and power-user booking endpoints.

These routes allow privileged roles (e.g., admins, facility managers) to:

* List all bookings in the system.
* Create bookings with conflict overrides.
* Force-cancel existing bookings.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.init_db import get_db
from services.bookings.app import schemas
from services.bookings.app.dependencies import (
    get_current_user,
    require_roles,
    CurrentUser,
    ADMIN_OR_FM_OR_AUDITOR_ROLES,
    ADMIN_ROLES,
)
from services.bookings.app.service_layer import booking_service


router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.BookingRead],
    status_code=status.HTTP_200_OK,
)
def list_all_bookings(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles(ADMIN_OR_FM_OR_AUDITOR_ROLES)),
):
    """
    List all bookings in the system.

    Typically used by admin, facility manager, or auditor roles.
    """
    bookings = booking_service.list_all_bookings(db)
    return bookings


@router.post(
    "/override",
    response_model=schemas.BookingRead,
    status_code=status.HTTP_201_CREATED,
)
def create_booking_with_override(
    payload: schemas.BookingCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ADMIN_ROLES)),
):
    """
    Create a booking with administrative override.

    Any existing conflicting bookings are force-cancelled first, then the
    new booking is created and confirmed. This endpoint is reserved for
    administrators and is a concrete implementation of the "override
    conflicts" requirement.
    """
    try:
        booking = booking_service.create_booking(
            db,
            user_id=current_user.id,
            role=current_user.role,
            room_id=payload.room_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
            force_override=True,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return booking


@router.post(
    "/{booking_id}/force-cancel",
    response_model=schemas.BookingRead,
    status_code=status.HTTP_200_OK,
)
def force_cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(ADMIN_ROLES)),
):
    """
    Force-cancel a booking regardless of its owner.

    This endpoint is meant to model administrative resolution of conflicts
    and stuck states.
    """
    try:
        booking = booking_service.cancel_booking(
            db,
            booking_id=booking_id,
            caller_user_id=current_user.id,
            caller_role=current_user.role,
            force=True,
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
    return booking
