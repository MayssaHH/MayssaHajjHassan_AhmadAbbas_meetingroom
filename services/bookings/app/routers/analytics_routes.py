"""
Analytics endpoints for the Bookings service.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from services.bookings.app import schemas
from services.bookings.app.dependencies import (
    get_db,
    get_current_user,
    require_roles,
    CurrentUser,
    ADMIN_FM_AUDITOR_SERVICE,
)
from services.bookings.app.service_layer import booking_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/bookings/summary",
    response_model=schemas.BookingsSummaryResponse,
)
def bookings_summary(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles(ADMIN_FM_AUDITOR_SERVICE)),
):
    """
    Return aggregate booking counts (total, confirmed, cancelled).
    """
    return booking_service.get_bookings_summary(db)


@router.get(
    "/bookings/by-room",
    response_model=list[schemas.BookingsByRoomItem],
)
def bookings_by_room(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles(ADMIN_FM_AUDITOR_SERVICE)),
):
    """
    Return booking counts grouped by room and status.
    """
    return booking_service.get_bookings_by_room(db)
