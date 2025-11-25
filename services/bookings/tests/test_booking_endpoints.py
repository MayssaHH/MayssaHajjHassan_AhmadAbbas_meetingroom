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
            name="admin_user",
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


def _ensure_user(username: str, role: str = "regular") -> User:
    with TestingSessionLocal() as db:
        user = db.query(User).filter_by(username=username).first()
        if user is None:
            user = User(
                name=username,
                username=username,
                email=f"{username}@example.com",
                password_hash=get_password_hash("password123"),
                role=role,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user


def _clear_all_bookings() -> None:
    with TestingSessionLocal() as db:
        db.query(Booking).delete()
        db.commit()


def test_list_my_bookings_returns_created_entries() -> None:
    """
    ``GET /bookings/me`` should list bookings created by the caller.
    """
    _clear_all_bookings()
    user = _ensure_user("list_user")

    with TestingSessionLocal() as db:
        room = db.query(Room).filter_by(name="Room E").first()
        assert room is not None
        room_id = room.id
    token = _get_token(username=user.username, role=user.role, user_id=user.id)

    start = (datetime.now() + timedelta(days=40)).replace(microsecond=0)
    end = start + timedelta(hours=2)
    resp = client.post(
        "/bookings/",
        json={
            "room_id": room_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    created_id = resp.json()["id"]

    list_resp = client.get(
        "/bookings/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_resp.status_code == 200
    payload = list_resp.json()
    assert any(item["id"] == created_id for item in payload)


def test_update_booking_endpoint_allows_owner() -> None:
    """
    Owners should be able to update their booking time window.
    """
    _clear_all_bookings()
    user = _ensure_user("update_user")

    with TestingSessionLocal() as db:
        room = db.query(Room).filter_by(name="Room E").first()
        assert room is not None
        room_id = room.id
    token = _get_token(username=user.username, role=user.role, user_id=user.id)

    start = (datetime.now() + timedelta(days=41)).replace(microsecond=0)
    end = start + timedelta(hours=2)
    resp = client.post(
        "/bookings/",
        json={
            "room_id": room_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    booking_id = resp.json()["id"]

    new_start = start + timedelta(hours=3)
    new_end = new_start + timedelta(hours=1)
    update_resp = client.put(
        f"/bookings/{booking_id}",
        json={
            "start_time": new_start.isoformat(),
            "end_time": new_end.isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_resp.status_code == 200, update_resp.text
    body = update_resp.json()
    assert body["start_time"].startswith(new_start.isoformat())
    assert body["end_time"].startswith(new_end.isoformat())


def test_update_booking_endpoint_rejects_other_users() -> None:
    """
    A user must not update someone else's booking.
    """
    _clear_all_bookings()
    owner = _ensure_user("owner_user")
    intruder = _ensure_user("intruder_user")

    with TestingSessionLocal() as db:
        room = db.query(Room).filter_by(name="Room E").first()
        assert room is not None
        room_id = room.id
    owner_token = _get_token(owner.username, owner.role, owner.id)
    intruder_token = _get_token(intruder.username, intruder.role, intruder.id)

    start = (datetime.now() + timedelta(days=42)).replace(microsecond=0)
    end = start + timedelta(hours=1)
    resp = client.post(
        "/bookings/",
        json={
            "room_id": room_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    booking_id = resp.json()["id"]

    update_resp = client.put(
        f"/bookings/{booking_id}",
        json={
            "start_time": (start + timedelta(hours=2)).isoformat(),
            "end_time": (end + timedelta(hours=2)).isoformat(),
        },
        headers={"Authorization": f"Bearer {intruder_token}"},
    )
    assert update_resp.status_code == 403


def test_cancel_booking_endpoint_marks_status_cancelled() -> None:
    """
    Deleting a booking should set its status to ``cancelled``.
    """
    _clear_all_bookings()
    user = _ensure_user("cancel_user")

    with TestingSessionLocal() as db:
        room = db.query(Room).filter_by(name="Room E").first()
        assert room is not None
        room_id = room.id
    token = _get_token(user.username, user.role, user.id)

    start = (datetime.now() + timedelta(days=43)).replace(microsecond=0)
    end = start + timedelta(hours=1)
    resp = client.post(
        "/bookings/",
        json={
            "room_id": room_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    booking_id = resp.json()["id"]

    delete_resp = client.delete(
        f"/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_resp.status_code == 204

    with TestingSessionLocal() as db:
        refreshed = db.query(Booking).get(booking_id)
        assert refreshed is not None
        assert refreshed.status == "cancelled"


def test_create_booking_for_missing_room_returns_400() -> None:
    """
    Creating a booking for a nonexistent room should return HTTP 400.
    """
    _clear_all_bookings()
    user = _ensure_user("missing_room_user")
    token = _get_token(user.username, user.role, user.id)

    start = (datetime.now() + timedelta(days=44)).replace(microsecond=0)
    end = start + timedelta(hours=1)
    response = client.post(
        "/bookings/",
        json={
            "room_id": 9999,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "Room does not exist" in response.json()["detail"]


def test_update_booking_endpoint_not_found_returns_404() -> None:
    """
    Updating a nonexistent booking id should return HTTP 404.
    """
    user = _ensure_user("missing_booking_user")
    token = _get_token(user.username, user.role, user.id)

    start = (datetime.now() + timedelta(days=45)).replace(microsecond=0)
    end = start + timedelta(hours=1)
    response = client.put(
        "/bookings/99999",
        json={"start_time": start.isoformat(), "end_time": end.isoformat()},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_update_booking_endpoint_conflict_returns_409() -> None:
    """
    Updating a booking into a conflicting interval should return HTTP 409.
    """
    _clear_all_bookings()
    user = _ensure_user("conflict_updater")
    token = _get_token(user.username, user.role, user.id)

    with TestingSessionLocal() as db:
        room = db.query(Room).filter_by(name="Room E").first()
        assert room is not None
        room_id = room.id

    base_start = (datetime.now() + timedelta(days=46)).replace(microsecond=0)
    base_end = base_start + timedelta(hours=1)
    first = client.post(
        "/bookings/",
        json={
            "room_id": room_id,
            "start_time": base_start.isoformat(),
            "end_time": base_end.isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert first.status_code == 201

    second = client.post(
        "/bookings/",
        json={
            "room_id": room_id,
            "start_time": (base_end + timedelta(hours=1)).isoformat(),
            "end_time": (base_end + timedelta(hours=2)).isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    booking_id = second.json()["id"]

    conflict_resp = client.put(
        f"/bookings/{booking_id}",
        json={
            "start_time": (base_start + timedelta(minutes=15)).isoformat(),
            "end_time": (base_end + timedelta(minutes=15)).isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert conflict_resp.status_code == 409
