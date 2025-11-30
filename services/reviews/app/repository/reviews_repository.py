"""
Data-access helpers for the ``reviews`` table.

All direct SQLAlchemy interaction for the Reviews service lives here so
that higher layers (service and routers) remain focused on business
logic and HTTP concerns.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from db.schema import Review


def get_review_by_id(db: Session, review_id: int) -> Optional[Review]:
    """
    Retrieve a single review by its primary key.
    """
    return db.query(Review).filter(Review.id == review_id).first()


def list_reviews_for_room(db: Session, room_id: int) -> List[Review]:
    """
    Return all reviews for a given room ordered by creation time.
    """
    return (
        db.query(Review)
        .filter(Review.room_id == room_id)
        .order_by(Review.created_at.asc())
        .all()
    )


def list_flagged_reviews(db: Session) -> List[Review]:
    """
    Return all reviews that are currently flagged.
    """
    return (
        db.query(Review)
        .filter(Review.is_flagged.is_(True))
        .order_by(Review.created_at.asc())
        .all()
    )


def list_all_reviews(db: Session) -> List[Review]:
    """
    Return all reviews in the system ordered by creation time.
    """
    return (
        db.query(Review)
        .order_by(Review.created_at.desc())
        .all()
    )


def create_review(
    db: Session,
    *,
    user_id: int,
    room_id: int,
    rating: int,
    comment: str,
) -> Review:
    """
    Insert a new review into the database.
    """
    review = Review(
        user_id=user_id,
        room_id=room_id,
        rating=rating,
        comment=comment,
        is_flagged=False,
        is_visible=True,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def save_review(db: Session, review: Review) -> Review:
    """
    Persist modifications made to an existing review.
    """
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def delete_review(db: Session, review: Review) -> None:
    """
    Delete a review from the database.
    """
    db.delete(review)
    db.commit()
