"""
Simple in-memory rate limiter for selected endpoints.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Deque, Dict

from common.config import get_settings
from common.exceptions import RateLimitExceededError

_requests: Dict[str, Deque[float]] = {}


def check_rate_limit(key: str) -> None:
    """
    Enforce rate limit for the given key (user or IP + endpoint).
    """
    settings = get_settings()
    window = settings.rate_limit_window_sec
    limit = settings.rate_limit_max_requests

    now = time.time()
    bucket = _requests.setdefault(key, deque())

    # Remove entries outside the window
    while bucket and now - bucket[0] > window:
        bucket.popleft()

    if len(bucket) >= limit:
        raise RateLimitExceededError(
            f"Rate limit exceeded ({limit} requests per {window} seconds)."
        )

    bucket.append(now)
