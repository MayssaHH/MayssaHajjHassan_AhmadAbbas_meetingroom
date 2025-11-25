"""
Unit tests for the core booking service logic (no HTTP layer).
"""

from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path

# Ensure the project root is on sys.path so that `common` and `db` can be imported
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.schema import Base, Booking, User, Room
from services.bookings.app.service_layer import booking_service


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_bookings_core.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_module(module) -> None:  # noqa: D401
    """Create tables and seed basic data for all tests in this module."""
    # Drop and recreate tables to ensure clean state
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as db:
        # Clear existing bookings to avoid conflicts
        db.query(Booking).delete()
        
        # Seed one user and one room if they do not exist
        if not db.query(User).filter_by(username="alice").first():
            user = User(
                name="Alice",
                username="alice",
                email="alice@example.com",
                password_hash="hashed",
                role="regular",
            )
            db.add(user)
        if not db.query(Room).filter_by(name="Room A").first():
            room = Room(
                name="Room A",
                capacity=10,
                equipment="[]",
                location="Building A",
                status="active",
            )
            db.add(room)
        if not db.query(Room).filter_by(name="Room Z").first():
            room_z = Room(
                name="Room Z",
                capacity=10,
                equipment="[]",
                location="Building A",
                status="active",
            )
            db.add(room_z)
        db.commit()


def test_create_booking_without_conflict() -> None:
    """
    Creating a booking in an empty interval should succeed.
    """
    with TestingSessionLocal() as db:
        # Clear any existing bookings for this room
        db.query(Booking).delete()
        db.commit()
        
        user = db.query(User).filter_by(username="alice").first()
        room = db.query(Room).filter_by(name="Room A").first()
        assert user is not None
        assert room is not None

        # Use a future date to avoid conflicts with any existing bookings
        start = datetime.now() + timedelta(days=10)
        end = start + timedelta(hours=1)

        booking = booking_service.create_booking(
            db,
            user_id=user.id,
            role=user.role,
            room_id=room.id,
            start_time=start,
            end_time=end,
            force_override=False,
        )
        assert isinstance(booking, Booking)
        assert booking.user_id == user.id
        assert booking.room_id == room.id
        assert booking.status == "confirmed"


def test_conflicting_booking_raises_error() -> None:
    """
    Creating a second booking with overlapping interval should raise
    BookingConflictError when override is disabled.
    """
    with TestingSessionLocal() as db:
        # Clear any existing bookings for this room
        room_a = db.query(Room).filter_by(name="Room A").first()
        if room_a:
            db.query(Booking).filter_by(room_id=room_a.id).delete()
        db.commit()
        
        user = db.query(User).filter_by(username="alice").first()
        room = db.query(Room).filter_by(name="Room A").first()
        assert user is not None
        assert room is not None

        # Use a future date to avoid conflicts with any existing bookings
        start = datetime.now() + timedelta(days=11)
        end = start + timedelta(hours=1)

        # First booking
        booking_service.create_booking(
            db,
            user_id=user.id,
            role=user.role,
            room_id=room.id,
            start_time=start,
            end_time=end,
            force_override=False,
        )

        # Second overlapping booking
        try:
            booking_service.create_booking(
                db,
                user_id=user.id,
                role=user.role,
                room_id=room.id,
                start_time=start + timedelta(minutes=30),
                end_time=end + timedelta(minutes=30),
                force_override=False,
            )
            assert False, "Expected BookingConflictError"
        except booking_service.BookingConflictError:
            pass


def test_admin_override_cancels_conflicts() -> None:
    """
    When an admin creates a booking with override, conflicting bookings
    should be marked as cancelled.
    """
    with TestingSessionLocal() as db:
        # Clear any existing bookings for this room
        room_z = db.query(Room).filter_by(name="Room Z").first()
        if room_z:
            db.query(Booking).filter_by(room_id=room_z.id).delete()
        db.commit()
        
        # Seed admin user if needed
        admin = db.query(User).filter_by(username="admin").first()
        room = db.query(Room).filter_by(name="Room Z").first()
        if admin is None:
            admin = User(
                name="Admin User",
                username="admin",
                email="admin@example.com",
                password_hash="hashed",
                role="admin",
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
        assert room is not None

        # Use a future date to avoid conflicts with any existing bookings
        start = datetime.now() + timedelta(days=12)
        end = start + timedelta(hours=1)

        # Existing booking
        existing = booking_service.create_booking(
            db,
            user_id=admin.id,
            role=admin.role,
            room_id=room.id,
            start_time=start,
            end_time=end,
            force_override=False,
        )

        # Admin override overlapping the same interval
        new_booking = booking_service.create_booking(
            db,
            user_id=admin.id,
            role=admin.role,
            room_id=room.id,
            start_time=start + timedelta(minutes=15),
            end_time=end + timedelta(minutes=15),
            force_override=True,
        )

        db.refresh(existing)

        assert existing.status == "cancelled"
        assert new_booking.status == "confirmed"
        assert new_booking.id != existing.id
