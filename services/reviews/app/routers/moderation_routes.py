"""
HTTP endpoints for review moderation.

MODERATOR + ADMIN endpoints:
* Flag and unflag reviews
* View flagged reviews (reports)

These endpoints are accessible to both moderators and administrators.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas
from ..dependencies import (
    CurrentUser,
    get_db,
    require_moderator_or_admin,
)
from ..service_layer import reviews_service

router = APIRouter(prefix="/reviews", tags=["reviews-moderation"])


@router.post(
    "/{review_id}/flag",
    response_model=schemas.ReviewRead,
)
def flag_review(
    review_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_moderator_or_admin),
):
    """
    Mark a review as flagged.

    This is intended for handling inappropriate or suspicious content.
    """
    review = reviews_service.get_review(db, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found.",
        )

    review = reviews_service.flag_review(db, review)
    return review


@router.post(
    "/{review_id}/unflag",
    response_model=schemas.ReviewRead,
)
def unflag_review(
    review_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_moderator_or_admin),
):
    """
    Clear the flagged state from a review.
    """
    review = reviews_service.get_review(db, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found.",
        )

    review = reviews_service.unflag_review(db, review)
    return review


@router.get(
    "/flagged",
    response_model=List[schemas.ReviewRead],
)
def list_flagged_reviews(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_moderator_or_admin),
):
    """
    List all reviews that are currently flagged (reports).

    MODERATOR + ADMIN: View all flagged reviews for moderation review.
    This is the "reports" view for moderators.
    """
    reviews = reviews_service.list_flagged_reviews(db)
    return reviews
