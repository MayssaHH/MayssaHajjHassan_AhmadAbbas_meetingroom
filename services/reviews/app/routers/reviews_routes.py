"""
HTTP endpoints for creating, updating, deleting, and listing reviews.

This router is mounted under the ``/reviews`` prefix in
:mod:`app.main`.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas
from ..dependencies import (
    CurrentUser,
    get_db,
    require_authenticated,
    require_read_access,
    allow_owner_or_admin_or_moderator,
    rate_limit_by_user,
)
from common.rbac import ROLE_AUDITOR
from common.exceptions import ForbiddenError, NotFoundError, BadRequestError
from ..service_layer import reviews_service

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post(
    "",
    response_model=schemas.ReviewRead,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    payload: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_authenticated),
    _limit = Depends(rate_limit_by_user("create_review")),
):
    """
    Create a new review for a room.

    Any authenticated user may create a review. Input data is validated
    and sanitized before being stored.
    """
    if current_user.role == ROLE_AUDITOR:
        raise ForbiddenError("Auditors cannot create reviews.")
    review = reviews_service.create_review(
        db,
        author_user_id=current_user.id,
        payload=payload,
    )
    return review


@router.get(
    "/room/{room_id}",
    response_model=List[schemas.ReviewRead],
)
def get_reviews_for_room(
    room_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_read_access),
):
    """
    Return all reviews associated with the given room.

    Any authenticated user may access this endpoint.
    """
    reviews = reviews_service.list_reviews_for_room(db, room_id)
    return reviews


@router.put(
    "/{review_id}",
    response_model=schemas.ReviewRead,
)
def update_review(
    review_id: int,
    payload: schemas.ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_authenticated),
):
    """
    Update an existing review.

    Only the owner of the review (or later an admin, if extended) is
    allowed to modify it.
    """
    review = reviews_service.get_review(db, review_id)
    if review is None:
        raise NotFoundError("Review not found.", error_code="REVIEW_NOT_FOUND")

    allow_owner_or_admin_or_moderator(review.user_id, current_user)

    review = reviews_service.update_review(db, review=review, payload=payload)
    return review


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_authenticated),
):
    """
    Delete an existing review.

    Only the owner of the review is allowed to delete it.
    """
    review = reviews_service.get_review(db, review_id)
    if review is None:
        raise NotFoundError("Review not found.", error_code="REVIEW_NOT_FOUND")

    allow_owner_or_admin_or_moderator(review.user_id, current_user)

    from ..repository import reviews_repository

    reviews_repository.delete_review(db, review)
    return None
