"""
Pydantic schemas for the Rooms service.

These models describe the request and response payloads for the Rooms
API. They are independent from the SQLAlchemy ``Room`` ORM model
defined in :mod:`db.schema`.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


class RoomBase(BaseModel):
    """
    Base attributes shared by most room-related schemas.
    """

    name: str = Field(..., max_length=100)
    location: str = Field(..., max_length=100)
    capacity: int = Field(..., ge=1)
    equipment: List[str] = Field(
        default_factory=list,
        description="List of equipment items available in the room.",
    )
    status: str = Field(
        default="active",
        description="Static status of the room (e.g. active, out_of_service).",
    )


class RoomCreate(RoomBase):
    """
    Payload used when creating a new room.

    All fields from :class:`RoomBase` are required.
    """


class RoomUpdate(BaseModel):
    """
    Payload used to partially update an existing room.

    Each field is optional; only provided values will be applied.
    """

    name: Optional[str] = Field(default=None, max_length=100)
    location: Optional[str] = Field(default=None, max_length=100)
    capacity: Optional[int] = Field(default=None, ge=1)
    equipment: Optional[List[str]] = None
    status: Optional[str] = None


class RoomRead(RoomBase):
    """
    Representation of a room returned by the API.
    """

    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("equipment", mode="before")
    @classmethod
    def _ensure_equipment_list(cls, value):
        """
        Accept either comma-separated strings or real lists.

        The ORM model stores equipment as a CSV string, so this validator
        converts it back into a list for API responses.
        """

        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


class RoomStatusResponse(BaseModel):
    """
    Response model returned by ``GET /rooms/{id}/status``.
    """

    room_id: int
    static_status: str
    is_currently_booked: bool = Field(
        default=False,
        description="Indicates whether the room is currently booked for the requested time window.",
    )
