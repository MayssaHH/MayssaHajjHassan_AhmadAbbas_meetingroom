"""
db.schema
=========

SQLAlchemy ORM models for the Smart Meeting Room backend.

This module centralizes the relational database schema used by all
microservices (Users, Rooms, Bookings, Reviews). It exposes a shared
:class:`Base` declarative metadata object and four core models:

* :class:`User`
* :class:`Room`
* :class:`Booking`
* :class:`Review`

Later, each service will import only the models it logically owns,
while using HTTP-based inter-service communication for cross-service
operations.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """
    User account model.

    Represents a human or system account that can authenticate into the
    Smart Meeting Room platform.

    Fields
    ------
    id:
        Integer primary key.
    name:
        Full display name for the user.
    username:
        Unique login handle.
    email:
        Unique contact email address.
    password_hash:
        Hashed password (never store plain text).
    role:
        High-level role, e.g. ``admin``, ``regular``, ``facility_manager``,
        ``moderator``, ``auditor`` or ``service_account``.
    created_at:
        Timestamp when the user record was created.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")


class Room(Base):
    """
    Meeting room model.

    Fields
    ------
    id:
        Integer primary key.
    name:
        Human-readable room name, unique across the system.
    capacity:
        Maximum number of attendees.
    equipment:
        Comma-separated list or free-text description of equipment.
    location:
        Building / floor / area label.
    status:
        High-level lifecycle status, e.g. ``active`` or ``out_of_service``.
    created_at:
        Timestamp when the room record was created.
    """

    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    capacity = Column(Integer, nullable=False)
    equipment = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    bookings = relationship("Booking", back_populates="room", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="room", cascade="all, delete-orphan")


class Booking(Base):
    """
    Meeting room booking model.

    Represents a reservation of a specific :class:`Room` by a given
    :class:`User` over a time interval.

    Fields
    ------
    id:
        Integer primary key.
    user_id:
        Foreign key to :class:`User`.
    room_id:
        Foreign key to :class:`Room`.
    start_time:
        Start timestamp for the booking.
    end_time:
        End timestamp for the booking.
    status:
        Booking status such as ``pending``, ``confirmed`` or ``cancelled``.
    created_at:
        Timestamp when the booking record was created.
    """

    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="confirmed")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="bookings")
    room = relationship("Room", back_populates="bookings")


class Review(Base):
    """
    Room review model.

    Represents feedback provided by a user after using a room.

    Fields
    ------
    id:
        Integer primary key.
    user_id:
        Foreign key to :class:`User`.
    room_id:
        Foreign key to :class:`Room`.
    rating:
        Integer rating, typically between 1 and 5.
    comment:
        Optional free-text comment. Will be validated and sanitized.
    flagged:
        Boolean flag indicating moderation state for this review.
    created_at:
        Timestamp when the review was created.
    updated_at:
        Timestamp when the review was last modified.
    """

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    flagged = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="reviews")
    room = relationship("Room", back_populates="reviews")
