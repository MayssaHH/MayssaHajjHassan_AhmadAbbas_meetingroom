"""
Tests for user-management endpoints that go beyond authentication.

These tests verify that:

* Listing users is restricted to admins.
* A user can update his/her own profile.
* Non-admin users cannot change another user's role.
* Admin users can change roles for other users.
"""

from __future__ import annotations

from typing import Dict

from fastapi.testclient import TestClient


def _register_user(
    client: TestClient,
    *,
    username: str,
    role: str = "regular",
) -> Dict:
    """
    Helper to register a user with a given role.
    """
    payload = {
        "name": f"{username.capitalize()} Example",
        "username": username,
        "email": f"{username}@example.com",
        "password": "password123",
        "role": role,
    }
    response = client.post("/api/v1/users/register", json=payload)
    assert response.status_code in (200, 201)
    return response.json()


def _login(client: TestClient, username: str, password: str = "password123") -> str:
    """
    Helper to log in a user and return the access token.
    """
    response = client.post(
        "/api/v1/users/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


def test_list_users_admin_only(client: TestClient) -> None:
    """
    Only admin users should be allowed to list all users.
    """
    _register_user(client, username="admin", role="admin")
    _register_user(client, username="bob", role="regular")

    # Admin call
    admin_token = _login(client, "admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    admin_response = client.get("/api/v1/users", headers=admin_headers)
    assert admin_response.status_code == 200
    users = admin_response.json()
    assert isinstance(users, list)
    assert any(u["username"] == "admin" for u in users)

    # Regular user call
    regular_token = _login(client, "bob")
    regular_headers = {"Authorization": f"Bearer {regular_token}"}
    regular_response = client.get("/api/v1/users", headers=regular_headers)
    # Either 401 or 403 is acceptable for "not allowed".
    assert regular_response.status_code in (401, 403)


def test_update_own_profile_works(client: TestClient) -> None:
    """
    A regular user can update his/her own profile via ``/users/me``.
    """
    _register_user(client, username="carol", role="regular")
    token = _login(client, "carol")
    headers = {"Authorization": f"Bearer {token}"}

    update_payload = {
        "name": "Carol Updated",
        "email": "carol.updated@example.com",
    }
    response = client.put("/api/v1/users/me", json=update_payload, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Carol Updated"
    assert data["email"] == "carol.updated@example.com"


def test_non_admin_cannot_change_other_user_role(client: TestClient) -> None:
    """
    A non-admin user must not be able to change someone else's role.
    """
    _register_user(client, username="dave", role="regular")
    target = _register_user(client, username="erin", role="regular")

    user_token = _login(client, "dave")
    headers = {"Authorization": f"Bearer {user_token}"}

    response = client.patch(
        f"/api/v1/users/{target['id']}/role",
        json={"role": "admin"},
        headers=headers,
    )
    assert response.status_code in (401, 403)


def test_admin_can_change_user_role(client: TestClient) -> None:
    """
    An admin user can change another user's role.
    """
    _register_user(client, username="superadmin", role="admin")
    target = _register_user(client, username="frank", role="regular")

    admin_token = _login(client, "superadmin")
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.patch(
        f"/api/v1/users/{target['id']}/role",
        json={"role": "moderator"},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "moderator"


def test_update_profile_rejects_duplicate_email(client: TestClient) -> None:
    """
    Updating to an email already in use should return HTTP 400.
    """
    _register_user(client, username="alice", role="regular")
    _register_user(client, username="bruce", role="regular")

    token = _login(client, "bruce")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.put(
        "/users/me",
        json={"email": "alice@example.com"},
        headers=headers,
    )
    assert response.status_code == 400
    assert "Email is already in use." in response.json()["detail"]


def test_update_profile_rejects_duplicate_username(client: TestClient) -> None:
    """
    Updating to an existing username should return HTTP 400.
    """
    _register_user(client, username="charlie", role="regular")
    _register_user(client, username="diana", role="regular")

    token = _login(client, "diana")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.put(
        "/users/me",
        json={"username": "charlie"},
        headers=headers,
    )
    assert response.status_code == 400
    assert "Username is already taken." in response.json()["detail"]


def test_admin_role_update_rejects_invalid_role(client: TestClient) -> None:
    """
    Admin role updates should validate the requested role value.
    """
    _register_user(client, username="chiefadmin", role="admin")
    target = _register_user(client, username="eve", role="regular")

    admin_token = _login(client, "chiefadmin")
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.patch(
        f"/api/v1/users/{target['id']}/role",
        json={"role": "superhero"},
        headers=headers,
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any("Input should be" in item["msg"] for item in detail)
