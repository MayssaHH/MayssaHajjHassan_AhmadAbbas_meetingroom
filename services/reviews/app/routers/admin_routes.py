"""
Administrator endpoints for the Reviews service.

These routes are organized by permission level:

ADMIN-ONLY endpoints:
* List all reviews in the system
* Delete reviews (permanent removal)
* Restore reviews (make hidden reviews visible again)

MODERATOR + ADMIN endpoints:
* Flag and unflag reviews
* Control review visibility (hide/show)
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas
from ..dependencies import (
    CurrentUser,
    get_db,
    require_admin_only,
    require_moderator_or_admin,
)
from ..repository import reviews_repository
from ..service_layer import reviews_service

router = APIRouter()


# ============================================================================
# ADMIN-ONLY ENDPOINTS
# ============================================================================

@router.get(
    "/reviews",
    response_model=List[schemas.ReviewRead],
)
def list_all_reviews(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_admin_only),
):
    """
    List all reviews in the system.

    ADMIN-ONLY: This endpoint shows all reviews regardless of visibility or flag status.
    """
    reviews = reviews_service.list_all_reviews(db)
    return reviews


@router.delete(
    "/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_review_admin(
    review_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_admin_only),
):
    """
    Permanently delete a review from the system.

    ADMIN-ONLY: This is a hard delete that removes the review from the database.
    Use hide/show for temporary removal that can be restored.
    """
    review = reviews_service.get_review(db, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found.",
        )

    reviews_repository.delete_review(db, review)
    return None


@router.post(
    "/reviews/{review_id}/restore",
    response_model=schemas.ReviewRead,
)
@router.patch(
    "/reviews/{review_id}/restore",
    response_model=schemas.ReviewRead,
)
def restore_review(
    review_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_admin_only),
):
    """
    Restore a hidden review (make it visible again).

    ADMIN-ONLY: This makes a previously hidden review visible to the public again.
    Supports both POST and PATCH methods.
    """
    review = reviews_service.get_review(db, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found.",
        )

    review = reviews_service.show_review(db, review)
    return review


# ============================================================================
# MODERATOR + ADMIN ENDPOINTS
# ============================================================================


@router.api_route(
    "/reviews/{review_id}/flag",
    methods=["POST", "PATCH"],
    response_model=schemas.ReviewRead,
)
def flag_review(
    review_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_moderator_or_admin),
):
    """
    Mark a review as flagged.

    MODERATOR + ADMIN: Flag inappropriate or suspicious content for review.
    Supports both POST and PATCH methods.
    """
    review = reviews_service.get_review(db, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found.",
        )

    review = reviews_service.flag_review(db, review)
    return review


@router.api_route(
    "/reviews/{review_id}/unflag",
    methods=["POST", "PATCH"],
    response_model=schemas.ReviewRead,
)
def unflag_review(
    review_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_moderator_or_admin),
):
    """
    Clear the flagged state from a review.

    MODERATOR + ADMIN: Remove the flag from a review after review.
    Supports both POST and PATCH methods.
    """
    review = reviews_service.get_review(db, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found.",
        )

    review = reviews_service.unflag_review(db, review)
    return review


@router.api_route(
    "/reviews/{review_id}/hide",
    methods=["POST", "PATCH"],
    response_model=schemas.ReviewRead,
)
def hide_review(
    review_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_moderator_or_admin),
):
    """
    Hide a review from public view.

    MODERATOR + ADMIN: Hide a review temporarily. Can be restored by admin.
    Supports both POST and PATCH methods.
    """
    review = reviews_service.get_review(db, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found.",
        )

    review = reviews_service.hide_review(db, review)
    return review


@router.api_route(
    "/reviews/{review_id}/show",
    methods=["POST", "PATCH"],
    response_model=schemas.ReviewRead,
)
def show_review(
    review_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_moderator_or_admin),
):
    """
    Make a hidden review visible again.

    MODERATOR + ADMIN: Restore visibility of a previously hidden review.
    Supports both POST and PATCH methods.
    """
    review = reviews_service.get_review(db, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found.",
        )

    review = reviews_service.show_review(db, review)
    return review

