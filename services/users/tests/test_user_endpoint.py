"""
Functional tests for user management endpoints of the Users service.
"""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.schema import Base
from services.users.app.main import app
from services.users.app.dependencies import get_db
from common.auth import get_password_hash
from db.schema import User


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_users_admin.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, future=True
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """
    Override dependency to use a separate SQLite database for tests.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Prepare tables and seed an admin user for tests
Base.metadata.create_all(bind=engine)

admin_password_hash = get_password_hash("adminpass")

with TestingSessionLocal() as db:
    admin = User(
        username="admin",
        email="admin@example.com",
        hashed_password=admin_password_hash,
        role="admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    ADMIN_ID = admin.id  # noqa: N816


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def get_admin_token() -> str:
    """
    Helper to obtain a JWT token for the seeded admin user.
    """
    response = client.post(
        "/users/login",
        json={"username": "admin", "password": "adminpass"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_admin_can_list_users() -> None:
    """
    Verify that an admin can list all users.
    """
    token = get_admin_token()
    response = client.get(
        "/users/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert any(u["username"] == "admin" for u in data)


def test_regular_user_cannot_list_users() -> None:
    """
    Verify that a regular user cannot list all users.
    """
    # Register regular user
    reg_resp = client.post(
        "/users/register",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "secret123",
        },
    )
    assert reg_resp.status_code == 201, reg_resp.text

    login_resp = client.post(
        "/users/login",
        json={"username": "bob", "password": "secret123"},
    )
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]

    response = client.get(
        "/users/",
        headers={"Authorization": f"Bearer {token}"},
    )
    # Should be forbidden
    assert response.status_code == 403


def test_update_own_profile() -> None:
    """
    Verify that a user can update their own profile.
    """
    # Register new user
    reg_resp = client.post(
        "/users/register",
        json={
            "username": "charlie",
            "email": "charlie@example.com",
            "password": "secret123",
        },
    )
    assert reg_resp.status_code == 201, reg_resp.text

    login_resp = client.post(
        "/users/login",
        json={"username": "charlie", "password": "secret123"},
    )
    token = login_resp.json()["access_token"]

    # Update email
    update_resp = client.put(
        "/users/me",
        json={"email": "charlie_new@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_resp.status_code == 200, update_resp.text
    data = update_resp.json()
    assert data["email"] == "charlie_new@example.com"
