"""
Analytics endpoints for the Reviews service.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from services.reviews.app.dependencies import CurrentUser, get_db, get_current_user
from services.reviews.app.service_layer import reviews_service
from common.rbac import (
    ROLE_ADMIN,
    ROLE_MODERATOR,
    ROLE_FACILITY_MANAGER,
    ROLE_AUDITOR,
    has_role,
)


class AverageRatingItem(BaseModel):
    room_id: int
    avg_rating: float
    review_count: int


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/reviews/average-rating-by-room",
    response_model=list[AverageRatingItem],
)
def average_rating_by_room(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Return average rating and review count grouped by room.
    """
    if not has_role(
        current_user.role,
        [ROLE_ADMIN, ROLE_MODERATOR, ROLE_FACILITY_MANAGER, ROLE_AUDITOR],
    ):
        from common.exceptions import ForbiddenError
        raise ForbiddenError("Insufficient permissions for analytics.")
    return reviews_service.get_average_rating_by_room(db)
