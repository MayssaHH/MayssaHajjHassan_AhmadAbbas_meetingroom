"""
Pydantic schemas for the Bookings service.

These models define the request and response payloads for the booking APIs,
decoupling external representations from internal database models.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BookingBase(BaseModel):
    """
    Base fields shared by booking creation and update payloads.
    """

    room_id: int = Field(..., description="Identifier of the room to be booked.")
    start_time: datetime = Field(
        ...,
        description="Start time of the booking (ISO 8601).",
    )
    end_time: datetime = Field(
        ...,
        description="End time of the booking (ISO 8601). Must be after start_time.",
    )


class BookingCreate(BookingBase):
    """
    Payload used to create a new booking.

    The user identifier is inferred from the authenticated principal and is
    not provided explicitly in the request body.
    """

    pass


class BookingUpdate(BaseModel):
    """
    Payload used to update an existing booking.

    Times are optional to allow partial updates. Status is reserved for
    administrative overrides and is NOT accepted from regular users.
    """

    start_time: Optional[datetime] = Field(
        None,
        description="New start time for the booking.",
    )
    end_time: Optional[datetime] = Field(
        None,
        description="New end time for the booking.",
    )


class BookingRead(BaseModel):
    """
    Booking representation returned by the API.

    It includes the owner (user_id), the room, the time window,
    and the current booking status.
    """

    id: int = Field(..., description="Primary key of the booking.")
    user_id: int = Field(..., description="Identifier of the booking owner.")
    room_id: int = Field(..., description="Identifier of the booked room.")
    start_time: datetime = Field(..., description="Start time of the booking.")
    end_time: datetime = Field(..., description="End time of the booking.")
    status: str = Field(..., description="Current status of the booking.")

    class Config:
        """
        Enable ORM mode so SQLAlchemy models can be returned directly.
        """

        from_attributes = True


class BookingsSummaryResponse(BaseModel):
    total_bookings: int
    confirmed_bookings: int
    cancelled_bookings: int


class BookingsByRoomItem(BaseModel):
    room_id: int
    total: int
    confirmed: int
    cancelled: int
