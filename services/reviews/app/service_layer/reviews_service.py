"""
Business logic for the Reviews service.

This module sits between the FastAPI routers and the low-level
repository functions. It knows how to:

* sanitize and validate review comments,
* enforce rating constraints (1..5),
* orchestrate inter-service validation (user/room/booking),
* implement moderation behaviour (flagging and unflagging).
"""

from __future__ import annotations

import re
from typing import List, Optional

from sqlalchemy.orm import Session

from .. import schemas
from ..repository import reviews_repository
from ..clients import users_client, rooms_client, bookings_client
from db.schema import Review
from common.config import get_settings


_HTML_TAG_RE = re.compile(r"<[^>]+>")
_PROFANITY = {"spamword", "offensive"}  # simple placeholder list


def _sanitize_comment(comment: str) -> str:
    """
    Sanitize a review comment.

    Steps applied:

    * Strip leading/trailing whitespace.
    * Remove simple HTML tags using a regular expression.
    * Collapse consecutive whitespace characters into a single space.

    Returns a safe, normalized string. If the result is empty, the
    caller may decide to reject the comment.
    """
    text = comment.strip()
    text = _HTML_TAG_RE.sub("", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _contains_profanity(comment: str) -> bool:
    lowered = comment.lower()
    return any(token in lowered for token in _PROFANITY)


def create_review(
    db: Session,
    *,
    author_user_id: int,
    payload: schemas.ReviewCreate,
) -> Review:
    """
    Create a new review for a room.

    The caller must already be authenticated. This function performs:

    * user existence validation (via Users client),
    * room state validation (via Rooms client),
    * optional booking check (via Bookings client),
    * comment sanitization.

    Raises :class:`ValueError` for invalid data.
    """
    settings = get_settings()
    if not users_client.ensure_user_exists(author_user_id):
        raise ValueError("User does not exist.")

    if not rooms_client.ensure_room_is_active(payload.room_id):
        raise ValueError("Room is not active or does not exist.")

    # Optional business rule: user must have at least one booking
    if settings.require_booking_for_review and not bookings_client.user_has_booking_for_room(
        author_user_id, payload.room_id
    ):
        raise ValueError("A booking is required to review this room.")

    comment = _sanitize_comment(payload.comment)
    if not comment:
        raise ValueError("Comment cannot be empty after sanitization.")
    if _contains_profanity(comment):
        raise ValueError("Comment contains inappropriate language.")

    review = reviews_repository.create_review(
        db,
        user_id=author_user_id,
        room_id=payload.room_id,
        rating=payload.rating,
        comment=comment,
    )
    return review


def update_review(
    db: Session,
    *,
    review: Review,
    payload: schemas.ReviewUpdate,
) -> Review:
    """
    Apply updates to an existing review.

    Only non-``None`` fields are applied. Comment updates are sanitized
    using the same logic as in :func:`create_review`.
    """
    if payload.rating is not None:
        review.rating = payload.rating

    if payload.comment is not None:
        sanitized = _sanitize_comment(payload.comment)
        if not sanitized:
            raise ValueError("Comment cannot be empty after sanitization.")
        review.comment = sanitized

    review = reviews_repository.save_review(db, review)
    return review


def get_review(db: Session, review_id: int) -> Optional[Review]:
    """
    Retrieve a review by id or return ``None`` if it does not exist.
    """
    return reviews_repository.get_review_by_id(db, review_id)


def list_reviews_for_room(db: Session, room_id: int) -> List[Review]:
    """
    Return all reviews for a given room.
    """
    return reviews_repository.list_reviews_for_room(db, room_id)


def list_flagged_reviews(db: Session) -> List[Review]:
    """
    Return all reviews currently marked as flagged.
    """
    return reviews_repository.list_flagged_reviews(db)


def list_all_reviews(db: Session) -> List[Review]:
    """
    Return all reviews in the system.
    """
    return reviews_repository.list_all_reviews(db)


def flag_review(db: Session, review: Review) -> Review:
    """
    Mark the given review as flagged.
    """
    review.is_flagged = True
    return reviews_repository.save_review(db, review)


def unflag_review(db: Session, review: Review) -> Review:
    """
    Clear the flagged state of the given review.
    """
    review.is_flagged = False
    return reviews_repository.save_review(db, review)


def hide_review(db: Session, review: Review) -> Review:
    """
    Hide the given review from public view.
    """
    review.is_visible = False
    return reviews_repository.save_review(db, review)


def show_review(db: Session, review: Review) -> Review:
    """
    Make the given review visible to the public.
    """
    review.is_visible = True
    return reviews_repository.save_review(db, review)


__all__ = [
    "create_review",
    "update_review",
    "get_review",
    "list_reviews_for_room",
    "list_flagged_reviews",
    "list_all_reviews",
    "flag_review",
    "unflag_review",
    "hide_review",
    "show_review",
]
