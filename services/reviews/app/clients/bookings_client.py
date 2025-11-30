"""
Bookings service client for the Reviews service.
"""

from __future__ import annotations

import httpx

from common.config import get_settings
from common.http_client import ServiceHTTPClient
from common.logging_utils import get_logger
from common.service_account import get_service_account_token

_logger = get_logger(__name__)


def user_has_booking_for_room(user_id: int, room_id: int) -> bool:
    """
    Return whether the given user has (or had) a booking for the room.

    Falls back to ``True`` when stub fallback is enabled.
    """
    settings = get_settings()
    token = get_service_account_token()
    client = ServiceHTTPClient(
        settings.bookings_service_url,
        timeout=settings.http_client_timeout,
        default_headers={"Authorization": f"Bearer {token}"},
        service_name="bookings",
    )
    try:
        resp = client.get(f"/admin/bookings/user/{user_id}/room/{room_id}")
        resp.raise_for_status()
        data = resp.json()
        return len(data) > 0
    except httpx.HTTPError as exc:
        if settings.client_stub_fallback:
            _logger.warning("Fallback allow for booking check user=%s room=%s: %s", user_id, room_id, exc)
            return True
        raise
