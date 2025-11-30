"""
Service account management for inter-service communication.

The project specification defines a *service account* role that is used by
non-human clients (i.e., other microservices) to call protected APIs with
the least privilege required. :contentReference[oaicite:6]{index=6}  

This module will be responsible for:

* Logging in to the Users service using service account credentials.
* Caching the resulting JWT access token in memory.
* Refreshing the token when it is about to expire.
* Providing helper functions that other services can use to attach the
  service account token to outgoing HTTP requests.
"""

from __future__ import annotations

import time
from typing import Optional, Tuple

from common.auth import create_access_token, verify_access_token
from common.config import get_settings
from common.logging_utils import get_logger


_SERVICE_ACCOUNT_TOKEN: Optional[str] = None
_SERVICE_ACCOUNT_EXP: Optional[float] = None
_logger = get_logger(__name__)


def _generate_token() -> Tuple[str, float]:
    """
    Create a short-lived service account token.

    We mint the token locally using the configured service-account username and
    the ``service_account`` role so that inter-service calls can authenticate
    without requiring a live Users login endpoint. The subject is set to ``0``
    to satisfy int conversions in downstream dependencies.
    """
    settings = get_settings()
    token = create_access_token(
        {"username": settings.service_account_username},
        subject="0",
        role="service_account",
        expires_delta=None,
    )
    payload = verify_access_token(token)
    exp_ts = payload.get("exp", time.time() + settings.access_token_expire_minutes * 60)
    return token, float(exp_ts)


def get_service_account_token(force_refresh: bool = False) -> str:
    """
    Return a cached service account JWT token, refreshing when near expiry.
    """
    global _SERVICE_ACCOUNT_TOKEN, _SERVICE_ACCOUNT_EXP  # noqa: PLW0603
    settings = get_settings()
    if not settings.service_account_enabled:
        raise RuntimeError("Service account usage is disabled by configuration.")

    now = time.time()
    refresh_threshold = 30  # seconds before expiry
    if (
        force_refresh
        or _SERVICE_ACCOUNT_TOKEN is None
        or _SERVICE_ACCOUNT_EXP is None
        or (_SERVICE_ACCOUNT_EXP - now) < refresh_threshold
    ):
        _SERVICE_ACCOUNT_TOKEN, _SERVICE_ACCOUNT_EXP = _generate_token()
        _logger.info("Refreshed service account token")
    return _SERVICE_ACCOUNT_TOKEN
