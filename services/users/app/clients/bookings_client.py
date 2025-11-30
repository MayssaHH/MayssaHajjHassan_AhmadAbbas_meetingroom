"""
Client utilities for interacting with the Bookings service.
"""

from __future__ import annotations

from typing import Any, Dict, List

import httpx

from common.config import get_settings
from common.http_client import ServiceHTTPClient
from common.logging_utils import get_logger
from common.service_account import get_service_account_token

_logger = get_logger(__name__)


def fetch_user_bookings(user_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve the booking history for a specific user from the Bookings service.
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
        resp = client.get(f"/api/v1/admin/bookings/user/{user_id}")
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as exc:
        if settings.client_stub_fallback:
            _logger.warning("Fallback to empty booking history for user %s: %s", user_id, exc)
            return []
        raise
