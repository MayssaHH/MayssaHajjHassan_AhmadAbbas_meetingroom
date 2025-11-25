"""
Pydantic schemas for the Reviews service.

These models describe the request and response payloads for the Reviews
API. They are independent from the SQLAlchemy ``Review`` ORM model
defined in :mod:`db.schema`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReviewBase(BaseModel):
    """
    Base attributes shared by most review-related schemas.
    """

    room_id: int = Field(..., description="Identifier of the room being reviewed.")
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Numeric rating between 1 and 5 (inclusive).",
    )
    comment: str = Field(
        ...,
        max_length=500,
        description="User comment describing the room experience.",
    )


class ReviewCreate(ReviewBase):
    """
    Payload used when creating a new review.

    The ``user_id`` is taken from the JWT token and not exposed to the
    client in the request body.
    """


class ReviewUpdate(BaseModel):
    """
    Payload used to update an existing review.

    Each field is optional; only provided values will be applied.
    """

    rating: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Updated numeric rating between 1 and 5.",
    )
    comment: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Updated comment for the review.",
    )


class ReviewRead(BaseModel):
    """
    Representation of a review returned by the API.
    """

    id: int
    user_id: int
    room_id: int
    rating: int
    comment: str
    is_flagged: bool
    created_at: Optional[datetime] = None

    class Config:
        """
        Pydantic configuration.

        ``from_attributes`` allows automatic construction of this model
        from ORM objects returned by SQLAlchemy.
        """

        from_attributes = True
