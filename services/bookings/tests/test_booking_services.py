"""
Unit tests for the core booking service logic (no HTTP layer).
"""

from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import pytest
import sys
from pathlib import Path

# Ensure the project root is on sys.path so that `common` and `db` can be imported
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.schema import Base, Booking, User, Room
from services.bookings.app.service_layer import booking_service
from unittest.mock import patch, MagicMock


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
        db.query(Booking).delete()

        for username, role in (
            ("alice", "regular"),
            ("bob", "regular"),
            ("admin", "admin"),
        ):
            if not db.query(User).filter_by(username=username).first():
                db.add(
                    User(
                        name=username.title(),
                        username=username,
                        email=f"{username}@example.com",
                        password_hash="hashed",
                        role=role,
                    )
                )

        for room_name in ("Room A", "Room Z"):
            if not db.query(Room).filter_by(name=room_name).first():
                db.add(
                    Room(
                        name=room_name,
                        capacity=10,
                        equipment="[]",
                        location="Building A",
                        status="active",
                    )
                )
        db.commit()


def _clear_bookings(db: Session) -> None:
    db.query(Booking).delete()
    db.commit()


def test_create_booking_without_conflict() -> None:
    """
    Creating a booking in an empty interval should succeed.
    """
    with TestingSessionLocal() as db:
        _clear_bookings(db)
        
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
        _clear_bookings(db)
        
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
        _clear_bookings(db)
        
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


def test_create_booking_invalid_range_raises_value_error() -> None:
    """
    Creating a booking with an inverted time range should raise ValueError.
    """
    with TestingSessionLocal() as db:
        user = db.query(User).filter_by(username="alice").one()
        room = db.query(Room).filter_by(name="Room A").one()
        start = datetime.now() + timedelta(days=5)
        end = start - timedelta(hours=1)

        try:
            booking_service.create_booking(
                db,
                user_id=user.id,
                role=user.role,
                room_id=room.id,
                start_time=start,
                end_time=end,
                force_override=False,
            )
            assert False, "Expected ValueError for invalid time range"
        except ValueError:
            pass


def test_update_booking_conflict_detected() -> None:
    """
    Updating a booking to overlap another one should raise BookingConflictError.
    """
    with TestingSessionLocal() as db:
        _clear_bookings(db)

        user = db.query(User).filter_by(username="alice").one()
        room = db.query(Room).filter_by(name="Room A").one()

        start = datetime.now() + timedelta(days=20)
        end = start + timedelta(hours=1)
        first = booking_service.create_booking(
            db,
            user_id=user.id,
            role=user.role,
            room_id=room.id,
            start_time=start,
            end_time=end,
            force_override=False,
        )

        # Second booking to conflict with
        other = booking_service.create_booking(
            db,
            user_id=user.id,
            role=user.role,
            room_id=room.id,
            start_time=start + timedelta(hours=2),
            end_time=end + timedelta(hours=2),
            force_override=False,
        )

        try:
            booking_service.update_booking_time(
                db,
                booking_id=other.id,
                caller_user_id=user.id,
                caller_role=user.role,
                start_time=start,
                end_time=end,
            )
            assert False, "Expected BookingConflictError"
        except booking_service.BookingConflictError:
            pass


def test_cancel_booking_permission_enforced() -> None:
    """
    A user cannot cancel another user's booking unless they are admin.
    """
    with TestingSessionLocal() as db:
        _clear_bookings(db)

        alice = db.query(User).filter_by(username="alice").one()
        bob = db.query(User).filter_by(username="bob").one()
        room = db.query(Room).filter_by(name="Room Z").one()

        start = datetime.now() + timedelta(days=25)
        end = start + timedelta(hours=1)
        victim = booking_service.create_booking(
            db,
            user_id=alice.id,
            role=alice.role,
            room_id=room.id,
            start_time=start,
            end_time=end,
            force_override=False,
        )

        try:
            booking_service.cancel_booking(
                db,
                booking_id=victim.id,
                caller_user_id=bob.id,
                caller_role=bob.role,
                force=False,
            )
            assert False, "Expected BookingPermissionError"
        except booking_service.BookingPermissionError:
            pass

        # Admin force cancel should succeed
        admin = db.query(User).filter_by(username="admin").first()
        if admin is None:
            admin = User(
                name="Admin",
                username="admin",
                email="admin2@example.com",
                password_hash="hashed",
                role="admin",
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        cancelled = booking_service.cancel_booking(
            db,
            booking_id=victim.id,
            caller_user_id=admin.id,
            caller_role=admin.role,
            force=True,
        )
        assert cancelled.status == "cancelled"


def test_create_booking_nonexistent_room_raises_value_error() -> None:
    """
    The service should reject bookings for rooms that do not exist.
    """
    with TestingSessionLocal() as db:
        _clear_bookings(db)
        user = db.query(User).filter_by(username="alice").one()
        start = datetime.now() + timedelta(days=2)
        end = start + timedelta(hours=1)

        with pytest.raises(ValueError, match="Room does not exist"):
            booking_service.create_booking(
                db,
                user_id=user.id,
                role=user.role,
                room_id=9999,
                start_time=start,
                end_time=end,
                force_override=False,
            )


def test_create_booking_nonexistent_user_raises_value_error() -> None:
    """
    The service should reject bookings for users that do not exist.
    """
    with TestingSessionLocal() as db:
        _clear_bookings(db)
        room = db.query(Room).filter_by(name="Room A").one()
        start = datetime.now() + timedelta(days=3)
        end = start + timedelta(hours=1)

        with pytest.raises(ValueError, match="User does not exist"):
            booking_service.create_booking(
                db,
                user_id=9999,
                role="regular",
                room_id=room.id,
                start_time=start,
                end_time=end,
                force_override=False,
            )


def test_update_booking_different_room_no_conflict() -> None:
    """
    Updating a booking should only check conflicts within the same room.
    """
    with TestingSessionLocal() as db:
        _clear_bookings(db)
        user = db.query(User).filter_by(username="alice").one()
        room_a = db.query(Room).filter_by(name="Room A").one()
        room_z = db.query(Room).filter_by(name="Room Z").one()

        start = datetime.now() + timedelta(days=5)
        end = start + timedelta(hours=1)
        first = booking_service.create_booking(
            db,
            user_id=user.id,
            role=user.role,
            room_id=room_a.id,
            start_time=start,
            end_time=end,
            force_override=False,
        )

        second = booking_service.create_booking(
            db,
            user_id=user.id,
            role=user.role,
            room_id=room_z.id,
            start_time=start + timedelta(hours=2),
            end_time=end + timedelta(hours=2),
            force_override=False,
        )

        # Update second booking to overlap the first booking's window.
        updated = booking_service.update_booking_time(
            db,
            booking_id=second.id,
            caller_user_id=user.id,
            caller_role=user.role,
            start_time=start + timedelta(minutes=15),
            end_time=end + timedelta(minutes=15),
        )

        assert updated.id == second.id
        assert updated.start_time == start + timedelta(minutes=15)
        assert updated.room_id == room_z.id


def test_create_booking_sends_notification() -> None:
    """
    Creating a booking should trigger a notification with correct arguments.
    """
    with TestingSessionLocal() as db:
        _clear_bookings(db)
        
        user = db.query(User).filter_by(username="alice").first()
        room = db.query(Room).filter_by(name="Room A").first()
        assert user is not None
        assert room is not None
        
        # Record arguments passed to notification function
        notification_calls = []
        
        def fake_notification(user_email, room_name, start_time, end_time):
            """Fake notification function that records arguments."""
            notification_calls.append({
                "user_email": user_email,
                "room_name": room_name,
                "start_time": start_time,
                "end_time": end_time,
            })
        
        # Mock the clients to return user and room data
        with patch("services.bookings.app.service_layer.booking_service.users_client.get_user") as mock_get_user, \
             patch("services.bookings.app.service_layer.booking_service.rooms_client.get_room") as mock_get_room, \
             patch("services.bookings.app.service_layer.booking_service.send_booking_created_notification", side_effect=fake_notification):
            
            mock_get_user.return_value = {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "username": user.username,
            }
            mock_get_room.return_value = {
                "id": room.id,
                "name": room.name,
                "location": room.location,
                "capacity": room.capacity,
            }
            
            # Use a future date to avoid conflicts
            start = datetime.now() + timedelta(days=30)
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
            
            # Assert notification was called once
            assert len(notification_calls) == 1
            
            # Assert correct arguments
            call_args = notification_calls[0]
            assert call_args["user_email"] == user.email
            assert call_args["room_name"] == room.name
            assert call_args["start_time"] == booking.start_time
            assert call_args["end_time"] == booking.end_time


def test_cancel_booking_sends_notification() -> None:
    """
    Cancelling a booking should trigger a cancellation notification with correct arguments.
    """
    with TestingSessionLocal() as db:
        _clear_bookings(db)
        
        user = db.query(User).filter_by(username="alice").first()
        room = db.query(Room).filter_by(name="Room A").first()
        assert user is not None
        assert room is not None
        
        # Record arguments passed to notification function
        notification_calls = []
        
        def fake_notification(user_email, room_name, start_time, end_time):
            """Fake notification function that records arguments."""
            notification_calls.append({
                "user_email": user_email,
                "room_name": room_name,
                "start_time": start_time,
                "end_time": end_time,
            })
        
        # Create a booking first
        start = datetime.now() + timedelta(days=31)
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
        
        # Mock the clients to return user and room data
        with patch("services.bookings.app.service_layer.booking_service.users_client.get_user") as mock_get_user, \
             patch("services.bookings.app.service_layer.booking_service.rooms_client.get_room") as mock_get_room, \
             patch("services.bookings.app.service_layer.booking_service.send_booking_cancelled_notification", side_effect=fake_notification):
            
            mock_get_user.return_value = {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "username": user.username,
            }
            mock_get_room.return_value = {
                "id": room.id,
                "name": room.name,
                "location": room.location,
                "capacity": room.capacity,
            }
            
            # Cancel the booking
            cancelled_booking = booking_service.cancel_booking(
                db,
                booking_id=booking.id,
                caller_user_id=user.id,
                caller_role=user.role,
                force=False,
            )
            
            # Assert notification was called once
            assert len(notification_calls) == 1
            
            # Assert correct arguments
            call_args = notification_calls[0]
            assert call_args["user_email"] == user.email
            assert call_args["room_name"] == room.name
            assert call_args["start_time"] == cancelled_booking.start_time
            assert call_args["end_time"] == cancelled_booking.end_time
