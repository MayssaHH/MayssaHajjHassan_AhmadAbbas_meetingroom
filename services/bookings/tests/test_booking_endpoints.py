"""
Integration tests for the Bookings service HTTP API.
"""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path

# Ensure the project root is on sys.path so that `common` and `db` can be imported
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from common.auth import get_password_hash, create_access_token
from db.schema import Base, Booking, User, Room
from db.init_db import get_db
from services.bookings.app.main import app


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_bookings_api.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """
    Override dependency to use a dedicated SQLite test database.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply DB override and create tables
app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=engine)

# Seed users and rooms
with TestingSessionLocal() as db:
    if not db.query(User).filter_by(username="regular_user").first():
        regular = User(
            name="regular_user",
            username="regular_user",
            email="regular@example.com",
            password_hash=get_password_hash("password123"),
            role="regular",
        )
        db.add(regular)

    if not db.query(User).filter_by(username="admin_user").first():
        admin = User(
            username="admin_user",
            email="admin@example.com",
            password_hash=get_password_hash("adminpass"),
            role="admin",
        )
        db.add(admin)

    if not db.query(Room).filter_by(name="Room E").first():
        room = Room(
            name="Room E",
            capacity=8,
            equipment="[]",
            location="Building B",
            status="active",
        )
        db.add(room)

    db.commit()

client = TestClient(app)


def _get_token(username: str, role: str, user_id: int) -> str:
    """
    Helper to build JWTs for tests.

    Note: we skip the real login flow and go directly through the token
    creation helper for simplicity.
    """
    return create_access_token(subject=str(user_id), role=role)


def test_create_booking_endpoint() -> None:
    """
    Regular user should be able to create a non-conflicting booking.
    """
    with TestingSessionLocal() as db:
        # Clear any existing bookings for this room to avoid conflicts
        room_e = db.query(Room).filter_by(name="Room E").first()
        if room_e:
            db.query(Booking).filter_by(room_id=room_e.id).delete()
        db.commit()
        
        user = db.query(User).filter_by(username="regular_user").first()
        room = db.query(Room).filter_by(name="Room E").first()
        assert user is not None
        assert room is not None
        token = _get_token(user.username, user.role, user.id)
        
        # Extract IDs before session closes
        user_id = user.id
        room_id = room.id

    # Use a future date to avoid conflicts
    start = (datetime.now() + timedelta(days=30)).replace(microsecond=0)
    end = start + timedelta(hours=1)

    response = client.post(
        "/bookings/",
        json={
            "room_id": room_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["room_id"] == room_id
    assert data["user_id"] == user_id
    assert data["status"] == "confirmed"


def test_conflicting_booking_returns_409() -> None:
    """
    Creating a conflicting booking as a regular user should return HTTP 409.
    """
    with TestingSessionLocal() as db:
        # Clear any existing bookings for this room to avoid conflicts
        room_e = db.query(Room).filter_by(name="Room E").first()
        if room_e:
            db.query(Booking).filter_by(room_id=room_e.id).delete()
        db.commit()
        
        user = db.query(User).filter_by(username="regular_user").first()
        room = db.query(Room).filter_by(name="Room E").first()
        assert user is not None
        assert room is not None
        token = _get_token(user.username, user.role, user.id)
        
        # Extract IDs before session closes
        user_id = user.id
        room_id = room.id

        # Use a future date to avoid conflicts
        start = (datetime.now() + timedelta(days=31)).replace(microsecond=0)
        end = start + timedelta(hours=1)

        # First booking (base)
        from services.bookings.app.service_layer import booking_service

        booking_service.create_booking(
            db,
            user_id=user_id,
            role=user.role,
            room_id=room_id,
            start_time=start,
            end_time=end,
            force_override=False,
        )

    # Second overlapping booking via API
    response = client.post(
        "/bookings/",
        json={
            "room_id": room_id,
            "start_time": (start + timedelta(minutes=15)).isoformat(),
            "end_time": (end + timedelta(minutes=15)).isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409, response.text


def test_admin_override_endpoint() -> None:
    """
    Admin should be able to create a booking with override while cancelling
    conflicting bookings.
    """
    with TestingSessionLocal() as db:
        # Clear any existing bookings for this room to avoid conflicts
        room_e = db.query(Room).filter_by(name="Room E").first()
        if room_e:
            db.query(Booking).filter_by(room_id=room_e.id).delete()
        db.commit()
        
        admin = db.query(User).filter_by(username="admin_user").first()
        room = db.query(Room).filter_by(name="Room E").first()
        assert admin is not None
        assert room is not None
        admin_token = _get_token(admin.username, admin.role, admin.id)
        
        # Extract IDs before session closes
        admin_id = admin.id
        room_id = room.id

        # Use a future date to avoid conflicts
        start = (datetime.now() + timedelta(days=32)).replace(microsecond=0)
        end = start + timedelta(hours=1)

        from services.bookings.app.service_layer import booking_service

        existing = booking_service.create_booking(
            db,
            user_id=admin_id,
            role=admin.role,
            room_id=room_id,
            start_time=start,
            end_time=end,
            force_override=False,
        )
        db.refresh(existing)
        assert existing.status == "confirmed"
        existing_id = existing.id

    response = client.post(
        "/admin/bookings/override",
        json={
            "room_id": room_id,
            "start_time": (start + timedelta(minutes=10)).isoformat(),
            "end_time": (end + timedelta(minutes=20)).isoformat(),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201, response.text
    new_booking = response.json()
    assert new_booking["status"] == "confirmed"

    # Verify the original booking is now cancelled
    with TestingSessionLocal() as db:
        refreshed = db.query(Booking).get(existing_id)
        assert refreshed is not None
        assert refreshed.status == "cancelled"
