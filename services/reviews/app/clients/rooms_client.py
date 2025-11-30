"""
Rooms service client for the Reviews service.
"""

from __future__ import annotations

import httpx

from common.config import get_settings
from common.http_client import ServiceHTTPClient
from common.logging_utils import get_logger
from common.service_account import get_service_account_token

_logger = get_logger(__name__)


def ensure_room_is_active(room_id: int) -> bool:
    """
    Indicate whether the given room exists and is active.

    Falls back to ``True`` when stub fallback is enabled.
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
        resp = client.get(f"/rooms/{room_id}")
        if resp.status_code == 404:
            return False
        resp.raise_for_status()
        data = resp.json()
        return data.get("status", "active") == "active"
    except httpx.HTTPError as exc:
        if settings.client_stub_fallback:
            _logger.warning("Fallback allow for room existence (%s): %s", room_id, exc)
            return True
        raise
