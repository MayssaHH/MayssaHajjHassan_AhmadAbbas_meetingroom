"""
Users service client for the Bookings service.
"""

from __future__ import annotations

import httpx
from typing import Optional

from common.config import get_settings
from common.http_client import ServiceHTTPClient
from common.logging_utils import get_logger
from common.service_account import get_service_account_token

_logger = get_logger(__name__)


def get_user(user_id: int) -> Optional[dict]:
    """
    Retrieve user information by ID.

    Parameters
    ----------
    user_id:
        Identifier of the user to retrieve.

    Returns
    -------
    dict or None
        User data including email, or None if the user does not exist.
        The dict contains fields from UserRead schema: id, name, username, email, role, created_at.
    """
    settings = get_settings()
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
            return None
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as exc:
        _logger.error("Failed to fetch user %s: %s", user_id, exc)
        if settings.client_stub_fallback:
            _logger.warning("Fallback: returning None for user %s", user_id)
            return None
        raise

