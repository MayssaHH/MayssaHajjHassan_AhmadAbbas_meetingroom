"""
Client utilities for interacting with the Bookings service from Rooms.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import httpx

from common.config import get_settings
from common.http_client import ServiceHTTPClient
from common.logging_utils import get_logger
from common.service_account import get_service_account_token

_logger = get_logger(__name__)


def is_room_currently_booked(room_id: int, *, start_time: datetime | None = None, end_time: datetime | None = None) -> bool:
    """
    Indicate whether the given room is currently booked for the time window.

    Falls back to ``False`` on downstream failures when ``client_stub_fallback``
    is enabled in settings.
    """
    settings = get_settings()
    if start_time is None:
        start_time = datetime.utcnow()
    if end_time is None:
        end_time = start_time + timedelta(minutes=5)

    token = get_service_account_token()
    client = ServiceHTTPClient(
        settings.bookings_service_url,
        timeout=settings.http_client_timeout,
        default_headers={"Authorization": f"Bearer {token}"},
        service_name="bookings",
    )
    try:
        resp = client.get(
            "/api/v1/bookings/check-availability",
            params={
                "room_id": room_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return not data.get("available", False)
    except httpx.HTTPError as exc:
        if settings.client_stub_fallback:
            _logger.warning("Falling back to stub availability for room %s: %s", room_id, exc)
            return False
        raise
