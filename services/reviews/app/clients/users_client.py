"""
Users service client for the Reviews service.
"""

from __future__ import annotations

import httpx

from common.config import get_settings
from common.http_client import ServiceHTTPClient
from common.logging_utils import get_logger
from common.service_account import get_service_account_token

_logger = get_logger(__name__)


def ensure_user_exists(user_id: int) -> bool:
    """
    Indicate whether the given user exists.

    Falls back to ``True`` when stub fallback is enabled.
    """
    settings = get_settings()
    if settings.client_stub_fallback:
        return True
    token = get_service_account_token()
    client = ServiceHTTPClient(
        settings.users_service_url,
        timeout=settings.http_client_timeout,
        default_headers={"Authorization": f"Bearer {token}"},
        service_name="users",
    )
    try:
        resp = client.get(f"/api/v1/users/id/{user_id}")
        if resp.status_code == 404:
            return False
        resp.raise_for_status()
        return True
    except httpx.HTTPError as exc:
        if settings.client_stub_fallback:
            _logger.warning("Fallback allow for user existence (%s): %s", user_id, exc)
            return True
        raise
