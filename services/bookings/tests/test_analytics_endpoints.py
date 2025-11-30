from datetime import datetime, timedelta
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.schema import Base, Booking, User, Room  # noqa: E402
from services.bookings.app.main import app  # noqa: E402
from services.bookings.app.dependencies import get_db  # noqa: E402
from common.auth import create_access_token  # noqa: E402


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_bookings_analytics.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as db:
        admin = User(
            name="Admin",
            username="admin",
            email="admin@example.com",
            password_hash="hashed",
            role="admin",
        )
        user = User(
            name="User",
            username="user",
            email="user@example.com",
            password_hash="hashed",
            role="regular",
        )
        room1 = Room(name="R1", capacity=5, equipment="", location="HQ", status="active")
        room2 = Room(name="R2", capacity=5, equipment="", location="HQ", status="active")
        db.add_all([admin, user, room1, room2])
        db.commit()
        db.refresh(admin)
        db.refresh(user)
        db.refresh(room1)
        db.refresh(room2)

        now = datetime.utcnow()
        bookings = [
            Booking(user_id=user.id, room_id=room1.id, start_time=now, end_time=now + timedelta(hours=1), status="confirmed"),
            Booking(user_id=user.id, room_id=room1.id, start_time=now + timedelta(days=1), end_time=now + timedelta(days=1, hours=1), status="cancelled"),
            Booking(user_id=user.id, room_id=room2.id, start_time=now + timedelta(days=2), end_time=now + timedelta(days=2, hours=1), status="confirmed"),
        ]
        db.add_all(bookings)
        db.commit()


def _make_token(uid: int, role: str) -> str:
    return create_access_token(subject=str(uid), role=role)


def test_summary_requires_admin() -> None:
    token = _make_token(2, "regular")
    resp = client.get("/analytics/bookings/summary", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code in (401, 403)


def test_summary_admin_ok() -> None:
    token = _make_token(1, "admin")
    resp = client.get("/analytics/bookings/summary", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_bookings"] == 3
    assert data["confirmed_bookings"] == 2
    assert data["cancelled_bookings"] == 1


def test_by_room_admin_ok() -> None:
    token = _make_token(1, "admin")
    resp = client.get("/analytics/bookings/by-room", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    payload = {item["room_id"]: item for item in resp.json()}
    assert payload[1]["total"] == 2
    assert payload[1]["confirmed"] == 1
    assert payload[1]["cancelled"] == 1
    assert payload[2]["total"] == 1
    assert payload[2]["confirmed"] == 1
    assert payload[2]["cancelled"] == 0
