"""
Functional tests for authentication-related endpoints of the Users service.
"""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.schema import Base
from services.users.app.main import app
from services.users.app.dependencies import get_db


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_users_auth.db"

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


# Create tables for the test database
Base.metadata.create_all(bind=engine)

# Override the dependency in the FastAPI app
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_register_and_login_flow() -> None:
    """
    End-to-end test for user registration and login.
    """
    # Register
    response = client.post(
        "/users/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "secret123",
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data

    # Login
    response = client.post(
        "/users/login",
        json={"username": "alice", "password": "secret123"},
    )
    assert response.status_code == 200, response.text
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    access_token = token_data["access_token"]

    # /users/me
    me_response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 200, me_response.text
    me_data = me_response.json()
    assert me_data["username"] == "alice"
    assert me_data["email"] == "alice@example.com"
    assert me_data["role"] == "regular"
