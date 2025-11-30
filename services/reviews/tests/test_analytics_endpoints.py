from pathlib import Path
import sys

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.schema import Base, Review  # noqa: E402
from services.reviews.app.main import app  # noqa: E402
from services.reviews.app import dependencies  # noqa: E402
from common.auth import create_access_token  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_reviews_analytics.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[dependencies.get_db] = _override_get_db


def _make_token(user_id: int, role: str, username: str | None = None) -> str:
    if username is None:
        username = f"user_{user_id}"
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
    }
    return create_access_token(payload)


def setup_module(module) -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as db:
        samples = [
            Review(user_id=1, room_id=1, rating=5, comment="great", is_flagged=False),
            Review(user_id=2, room_id=1, rating=4, comment="good", is_flagged=False),
            Review(user_id=3, room_id=2, rating=3, comment="ok", is_flagged=False),
            Review(user_id=4, room_id=2, rating=3, comment="meh", is_flagged=False),
            Review(user_id=5, room_id=2, rating=4, comment="nice", is_flagged=False),
        ]
        db.add_all(samples)
        db.commit()


def test_average_rating_requires_privileged_role() -> None:
    client = TestClient(app)
    token = _make_token(10, "regular")
    resp = client.get(
        "/api/v1/analytics/reviews/average-rating-by-room",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code in (401, 403)


def test_average_rating_by_room_admin() -> None:
    client = TestClient(app)
    token = _make_token(1, "admin")
    resp = client.get(
        "/api/v1/analytics/reviews/average-rating-by-room",
        headers={"Authorization": f"Bearer $token".replace("$token", token)},
    )
    # Correction: use proper header
    resp = client.get(
        "/api/v1/analytics/reviews/average-rating-by-room",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = {item["room_id"]: item for item in resp.json()}
    assert len(data) == 2
    assert data[1]["avg_rating"] == 4.5
    assert data[1]["review_count"] == 2
    assert round(data[2]["avg_rating"], 2) == 3.33
    assert data[2]["review_count"] == 3
