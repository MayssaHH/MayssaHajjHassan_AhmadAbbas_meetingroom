import time
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.rate_limiter import check_rate_limit  # noqa: E402
from common.exceptions import RateLimitExceededError  # noqa: E402


def test_rate_limiter_window_resets(monkeypatch):
    from common import rate_limiter
    original_get_settings = rate_limiter.get_settings
    rate_limiter._requests.clear()

    class Dummy:
        rate_limit_window_sec = 1
        rate_limit_max_requests = 2

    rate_limiter.get_settings = lambda: Dummy()  # type: ignore
    try:
        key = "test:1"
        check_rate_limit(key)
        check_rate_limit(key)
        with pytest.raises(RateLimitExceededError):
            check_rate_limit(key)
        time.sleep(1.05)
        check_rate_limit(key)  # window expired
    finally:
        rate_limiter._requests.clear()
        rate_limiter.get_settings = original_get_settings  # type: ignore


def test_rate_limiter_isolated_keys(monkeypatch):
    from common import rate_limiter
    original_get_settings = rate_limiter.get_settings
    rate_limiter._requests.clear()

    class Dummy:
        rate_limit_window_sec = 2
        rate_limit_max_requests = 1

    rate_limiter.get_settings = lambda: Dummy()  # type: ignore
    try:
        check_rate_limit("user:1")
        # different key should not be affected
        check_rate_limit("user:2")
        with pytest.raises(RateLimitExceededError):
            check_rate_limit("user:1")
        time.sleep(2.1)
        check_rate_limit("user:1")  # after window, allowed again
    finally:
        rate_limiter._requests.clear()
        rate_limiter.get_settings = original_get_settings  # type: ignore
