"""
Endpoint-level tests for the Rooms service.

These tests verify:

* Role-based access control for room creation.
* Basic room listing and filtering.
* The structure of the room-status response.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from common.auth import create_access_token


def _make_token(user_id: int, role: str, username: str | None = None) -> str:
    """
    Helper to construct a JWT token with the minimal claims expected by
    :func:`services.rooms.app.dependencies.get_current_user`.
    """
    if username is None:
        username = f"user_{user_id}"
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
    }
    return create_access_token(payload)


def _create_room(
    client: TestClient,
    *,
    token: str,
    name: str,
    location: str = "HQ",
    capacity: int = 10,
    equipment: list[str] | None = None,
    status: str = "active",
) -> int:
    payload = {
        "name": name,
        "location": location,
        "capacity": capacity,
        "equipment": equipment or [],
        "status": status,
    }
    response = client.post(
        "/api/v1/rooms",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["id"]


def test_facility_manager_can_create_room(client: TestClient) -> None:
    """
    Facility managers should be allowed to create new rooms.
    """
    token = _make_token(user_id=1, role="facility_manager")

    payload = {
        "name": "Room A",
        "location": "Main Building",
        "capacity": 10,
        "equipment": ["projector", "whiteboard"],
        "status": "active",
    }
    response = client.post(
        "/api/v1/rooms",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    assert data["name"] == "Room A"
    assert data["capacity"] == 10
    assert "id" in data


def test_regular_user_cannot_create_room(client: TestClient) -> None:
    """
    Regular users should not be able to create rooms.
    """
    token = _make_token(user_id=2, role="regular")

    payload = {
        "name": "Room B",
        "location": "Main Building",
        "capacity": 5,
        "equipment": [],
        "status": "active",
    }
    response = client.post(
        "/api/v1/rooms",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    # Either 401 (unauthorized) or 403 (forbidden) are acceptable.
    assert response.status_code in (401, 403)


def test_filter_by_min_capacity(client: TestClient) -> None:
    """
    Filtering by minimum capacity should return only rooms that match.
    """
    token_manager = _make_token(user_id=1, role="facility_manager")

    # Create three rooms with different capacities.
    rooms_payloads = [
        {"name": "Small", "location": "B1", "capacity": 4},
        {"name": "Medium", "location": "B1", "capacity": 10},
        {"name": "Large", "location": "B1", "capacity": 20},
    ]

    for rp in rooms_payloads:
        body = {
            "name": rp["name"],
            "location": rp["location"],
            "capacity": rp["capacity"],
            "equipment": [],
            "status": "active",
        }
        resp = client.post(
            "/rooms",
            json=body,
            headers={"Authorization": f"Bearer {token_manager}"},
        )
        assert resp.status_code in (200, 201)

    # Regular user listing with min_capacity filter
    token_regular = _make_token(user_id=2, role="regular")
    response = client.get(
        "/api/v1/rooms",
        params={"min_capacity": 10},
        headers={"Authorization": f"Bearer {token_regular}"},
    )

    assert response.status_code == 200
    data = response.json()
    capacities = {room["capacity"] for room in data}
    assert capacities == {10, 20}


def test_room_status_endpoint_returns_static_status(client: TestClient) -> None:
    """
    ``GET /rooms/{id}/status`` should return at least the static status
    of the room and a boolean ``is_currently_booked`` field.
    """
    token_manager = _make_token(user_id=1, role="facility_manager")

    # Create a room
    payload = {
        "name": "StatusRoom",
        "location": "C1",
        "capacity": 8,
        "equipment": [],
        "status": "active",
    }
    create_resp = client.post(
        "/rooms",
        json=payload,
        headers={"Authorization": f"Bearer {token_manager}"},
    )
    assert create_resp.status_code in (200, 201)
    room_id = create_resp.json()["id"]

    token_regular = _make_token(user_id=2, role="regular")
    status_resp = client.get(
        f"/api/v1/rooms/{room_id}/status",
        headers={"Authorization": f"Bearer {token_regular}"},
    )

    assert status_resp.status_code == 200
    data = status_resp.json()

    assert data["room_id"] == room_id
    assert data["static_status"] == "active"
    assert isinstance(data["is_currently_booked"], bool)


def test_room_manager_can_update_room(client: TestClient) -> None:
    """
    Updating a room should be allowed for facility managers.
    """
    manager_token = _make_token(user_id=1, role="facility_manager")
    room_id = _create_room(
        client,
        token=manager_token,
        name="UpdateRoom",
        equipment=["tv"],
    )

    update_payload = {
        "location": "Annex",
        "capacity": 25,
        "equipment": ["tv", "mic"],
        "status": "out_of_service",
    }
    response = client.put(
        f"/api/v1/rooms/{room_id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["location"] == "Annex"
    assert body["capacity"] == 25
    assert sorted(body["equipment"]) == ["mic", "tv"]
    assert body["status"] == "out_of_service"


def test_regular_user_cannot_update_room(client: TestClient) -> None:
    """
    Regular users must not be able to update rooms.
    """
    manager_token = _make_token(user_id=1, role="facility_manager")
    room_id = _create_room(client, token=manager_token, name="BlockedRoom")

    regular_token = _make_token(user_id=2, role="regular")
    response = client.put(
        f"/api/v1/rooms/{room_id}",
        json={"capacity": 999},
        headers={"Authorization": f"Bearer {regular_token}"},
    )
    assert response.status_code in (401, 403)


def test_room_manager_can_delete_room(client: TestClient) -> None:
    """
    Facility managers should be able to delete rooms.
    """
    manager_token = _make_token(user_id=1, role="facility_manager")
    room_id = _create_room(client, token=manager_token, name="DeleteRoom")

    response = client.delete(
        f"/api/v1/rooms/{room_id}",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 204

    # Subsequent fetch should 404
    check = client.get(
        f"/api/v1/rooms/{room_id}",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert check.status_code == 404


def test_regular_user_cannot_delete_room(client: TestClient) -> None:
    """
    Regular users should not be able to delete rooms.
    """
    manager_token = _make_token(user_id=1, role="facility_manager")
    room_id = _create_room(client, token=manager_token, name="NoDeleteRoom")

    regular_token = _make_token(user_id=2, role="regular")
    response = client.delete(
        f"/api/v1/rooms/{room_id}",
        headers={"Authorization": f"Bearer {regular_token}"},
    )
    assert response.status_code in (401, 403)
