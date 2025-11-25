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
)
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
):
    """
    Create a new review for a room.

    Any authenticated user may create a review. Input data is validated
    and sanitized before being stored.
    """
    try:
        review = reviews_service.create_review(
            db,
            author_user_id=current_user.id,
            payload=payload,
        )
    except ValueError as exc:  # business validation error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return review


@router.get(
    "/room/{room_id}",
    response_model=List[schemas.ReviewRead],
)
def get_reviews_for_room(
    room_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_authenticated),
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found.",
        )

    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to edit this review.",
        )

    try:
        review = reviews_service.update_review(db, review=review, payload=payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found.",
        )

    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete this review.",
        )

    from ..repository import reviews_repository

    reviews_repository.delete_review(db, review)
    return None
