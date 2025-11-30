"""
Rooms service client for the Bookings service.
"""

from __future__ import annotations

import httpx
from typing import Optional

from common.config import get_settings
from common.http_client import ServiceHTTPClient
from common.logging_utils import get_logger
from common.service_account import get_service_account_token

_logger = get_logger(__name__)


def get_room(room_id: int) -> Optional[dict]:
    """
    Retrieve room information by ID.

    Parameters
    ----------
    room_id:
        Identifier of the room to retrieve.

    Returns
    -------
    dict or None
        Room data including name, or None if the room does not exist.
        The dict contains fields from RoomRead schema: id, name, location, capacity, equipment, status, created_at.
    """
    settings = get_settings()
    token = get_service_account_token()
    client = ServiceHTTPClient(
        settings.rooms_service_url,
        timeout=settings.http_client_timeout,
        default_headers={"Authorization": f"Bearer {token}"},
        service_name="rooms",
    )
    try:
        resp = client.get(f"/api/v1/rooms/{room_id}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as exc:
        _logger.error("Failed to fetch room %s: %s", room_id, exc)
        if settings.client_stub_fallback:
            _logger.warning("Fallback: returning None for room %s", room_id)
            return None
        raise

