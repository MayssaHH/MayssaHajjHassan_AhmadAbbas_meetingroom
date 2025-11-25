"""
Endpoint-level tests for the Reviews service.

These tests verify:

* Validation of rating and comment.
* Authentication requirements for creating/updating/deleting reviews.
* Ownership checks for update/delete.
* Moderator/Admin moderation behaviour (flagging and unflagging).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from common.auth import create_access_token


def _make_token(user_id: int, role: str, username: str | None = None) -> str:
    """
    Helper to construct a JWT token with the minimal claims expected by
    :func:`services.reviews.app.dependencies.get_current_user`.
    """
    if username is None:
        username = f"user_{user_id}"
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
    }
    return create_access_token(payload)


def test_valid_review_is_accepted(client: TestClient) -> None:
    """
    A valid review from an authenticated user should be accepted.
    """
    token = _make_token(user_id=1, role="regular")

    payload = {
        "room_id": 1,
        "rating": 5,
        "comment": "Great room, very clean!",
    }
    response = client.post(
        "/reviews",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    assert data["rating"] == 5
    assert data["room_id"] == 1
    assert data["user_id"] == 1
    assert data["is_flagged"] is False


def test_invalid_rating_is_rejected(client: TestClient) -> None:
    """
    A rating outside the range [1, 5] should be rejected by validation.
    """
    token = _make_token(user_id=2, role="regular")

    payload = {
        "room_id": 1,
        "rating": 6,  # invalid
        "comment": "Too good to be true",
    }
    response = client.post(
        "/reviews",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    # Pydantic validation error -> 422
    assert response.status_code == 422


def test_unauthenticated_cannot_create_update_delete(client: TestClient) -> None:
    """
    Unauthenticated callers should not be able to create, update, or
    delete reviews.
    """
    # Create without token
    create_resp = client.post(
        "/reviews",
        json={"room_id": 1, "rating": 4, "comment": "Nice"},
    )
    assert create_resp.status_code in (401, 403)

    # Try update without token (id=1 will not exist but auth fails first)
    update_resp = client.put(
        "/reviews/1",
        json={"rating": 3},
    )
    assert update_resp.status_code in (401, 403)

    # Try delete without token
    delete_resp = client.delete("/reviews/1")
    assert delete_resp.status_code in (401, 403)


def test_only_owner_can_update_and_delete(client: TestClient) -> None:
    """
    Only the owner of a review should be allowed to update or delete it.
    """
    owner_token = _make_token(user_id=10, role="regular", username="owner")
    other_token = _make_token(user_id=20, role="regular", username="other")

    # Owner creates review
    create_resp = client.post(
        "/reviews",
        json={"room_id": 1, "rating": 4, "comment": "Pretty good"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert create_resp.status_code in (200, 201)
    review_id = create_resp.json()["id"]

    # Other user tries to update
    update_resp = client.put(
        f"/reviews/{review_id}",
        json={"rating": 1},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert update_resp.status_code == 403

    # Other user tries to delete
    delete_resp = client.delete(
        f"/reviews/{review_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert delete_resp.status_code == 403

    # Owner can update
    owner_update = client.put(
        f"/reviews/{review_id}",
        json={"rating": 5},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert owner_update.status_code == 200
    assert owner_update.json()["rating"] == 5

    # Owner can delete
    owner_delete = client.delete(
        f"/reviews/{review_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert owner_delete.status_code == 204


def test_moderator_can_flag_and_unflag_review(client: TestClient) -> None:
    """
    Moderators (and admins) should be able to flag and unflag reviews.
    """
    regular_token = _make_token(user_id=30, role="regular")
    moderator_token = _make_token(user_id=40, role="moderator")

    # Regular user creates a review
    create_resp = client.post(
        "/reviews",
        json={"room_id": 2, "rating": 3, "comment": "It was okay."},
        headers={"Authorization": f"Bearer {regular_token}"},
    )
    assert create_resp.status_code in (200, 201)
    review_id = create_resp.json()["id"]

    # Moderator flags the review
    flag_resp = client.post(
        f"/reviews/{review_id}/flag",
        headers={"Authorization": f"Bearer {moderator_token}"},
    )
    assert flag_resp.status_code == 200
    assert flag_resp.json()["is_flagged"] is True

    # Moderator unflags the review
    unflag_resp = client.post(
        f"/reviews/{review_id}/unflag",
        headers={"Authorization": f"Bearer {moderator_token}"},
    )
    assert unflag_resp.status_code == 200
    assert unflag_resp.json()["is_flagged"] is False


def test_comment_is_sanitized(client: TestClient) -> None:
    """
    HTML tags in comments should be stripped by the sanitization logic.
    """
    token = _make_token(user_id=50, role="regular")

    payload = {
        "room_id": 3,
        "rating": 4,
        "comment": "<b>Nice</b> <script>alert('x')</script> room",
    }
    response = client.post(
        "/reviews",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    # we expect tags to be removed and spaces normalized
    assert "script" not in data["comment"]
    assert "<" not in data["comment"]
    assert ">" not in data["comment"]
    assert "Nice" in data["comment"]


def test_get_reviews_for_room_returns_created_entries(client: TestClient) -> None:
    """
    ``GET /reviews/room/{room_id}`` should return all reviews for that room.
    """
    token = _make_token(user_id=60, role="regular")
    for rating in (2, 4):
        resp = client.post(
            "/reviews",
            json={"room_id": 99, "rating": rating, "comment": f"rating {rating}"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code in (200, 201)

    response = client.get(
        "/reviews/room/99",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {item["rating"] for item in data} == {2, 4}


def test_flagged_reviews_listing_requires_moderator(client: TestClient) -> None:
    """
    Listing flagged reviews should be restricted to moderators/admins.
    """
    regular_token = _make_token(user_id=70, role="regular")
    moderator_token = _make_token(user_id=71, role="moderator")

    create_resp = client.post(
        "/reviews",
        json={"room_id": 5, "rating": 3, "comment": "meh"},
        headers={"Authorization": f"Bearer {regular_token}"},
    )
    review_id = create_resp.json()["id"]

    client.post(
        f"/reviews/{review_id}/flag",
        headers={"Authorization": f"Bearer {moderator_token}"},
    )

    forbidden = client.get(
        "/reviews/flagged",
        headers={"Authorization": f"Bearer {regular_token}"},
    )
    assert forbidden.status_code == 403

    allowed = client.get(
        "/reviews/flagged",
        headers={"Authorization": f"Bearer {moderator_token}"},
    )
    assert allowed.status_code == 200
    payload = allowed.json()
    assert any(item["id"] == review_id for item in payload)
