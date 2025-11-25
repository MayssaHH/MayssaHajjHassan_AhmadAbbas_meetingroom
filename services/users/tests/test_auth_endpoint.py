"""
Tests for authentication-related endpoints in the Users service.

The tests use a dedicated SQLite database configured in
``conftest.py`` so that they do not touch the development or
production database.
"""

from __future__ import annotations

from typing import Dict

from fastapi.testclient import TestClient


def _register_example_user(client: TestClient, username: str = "alice") -> Dict:
    """
    Helper that registers a user and returns the JSON response.

    Parameters
    ----------
    client:
        FastAPI test client.
    username:
        Username to use for the new account.

    Returns
    -------
    dict
        JSON payload returned by the registration endpoint.
    """
    payload = {
        "name": "Alice Example",
        "username": username,
        "email": f"{username}@example.com",
        "password": "password123",
        "role": "regular",
    }
    response = client.post("/users/register", json=payload)
    # Accept either 200 or 201 depending on how the endpoint is implemented.
    assert response.status_code in (200, 201)
    return response.json()


def test_registration_success(client: TestClient) -> None:
    """
    A new user can register successfully.
    """
    user = _register_example_user(client, username="alice")
    assert user["username"] == "alice"
    assert "id" in user
    assert user["role"] == "regular"


def test_registration_duplicate_username_fails(client: TestClient) -> None:
    """
    Registering twice with the same username should fail.
    """
    _register_example_user(client, username="bob")

    duplicate_payload = {
        "name": "Another Bob",
        "username": "bob",
        "email": "bob2@example.com",
        "password": "password123",
        "role": "regular",
    }
    response = client.post("/users/register", json=duplicate_payload)
    # Implementation may use 400 or 409; both indicate a conflict here.
    assert response.status_code in (400, 409)


def test_login_success_returns_token(client: TestClient) -> None:
    """
    Logging in with a valid username/password pair returns a JWT token.
    """
    _register_example_user(client, username="carol")

    login_payload = {"username": "carol", "password": "password123"}
    response = client.post("/users/login", json=login_payload)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    assert data.get("token_type") == "bearer"


def test_login_wrong_password_rejected(client: TestClient) -> None:
    """
    Logging in with an incorrect password should be rejected.
    """
    _register_example_user(client, username="dave")

    login_payload = {"username": "dave", "password": "wrong-password"}
    response = client.post("/users/login", json=login_payload)

    # 400 (bad credentials) or 401 (unauthorized) are both acceptable.
    assert response.status_code in (400, 401)


def test_me_requires_authentication(client: TestClient) -> None:
    """
    The ``/users/me`` endpoint must require authentication.
    """
    response = client.get("/users/me")
    # Either 401 or 403 depending on how auth is wired.
    assert response.status_code in (401, 403)


def test_me_returns_current_user(client: TestClient) -> None:
    """
    When authenticated, ``/users/me`` returns the current user's profile.
    """
    _register_example_user(client, username="erin")

    login_response = client.post(
        "/users/login",
        json={"username": "erin", "password": "password123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/users/me", headers=headers)

    assert me_response.status_code == 200
    data = me_response.json()
    assert data["username"] == "erin"
