"""
Simple in-memory circuit breaker used to protect inter-service HTTP calls.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict

from common.config import get_settings
from common.exceptions import CircuitOpenError


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    failure_threshold: int
    open_timeout: int
    half_open_max_calls: int

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_ts: float = 0.0
    half_open_attempts: int = 0

    def before_call(self) -> None:
        now = time.time()
        if self.state == CircuitState.OPEN:
            if now - self.last_failure_ts >= self.open_timeout:
                # Move to HALF_OPEN to probe downstream.
                self.state = CircuitState.HALF_OPEN
                self.half_open_attempts = 0
            else:
                raise CircuitOpenError("Circuit is open; skipping downstream call.")

        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_attempts >= self.half_open_max_calls:
                raise CircuitOpenError("Circuit is half-open and probe limit reached.")
            self.half_open_attempts += 1

    def record_success(self) -> None:
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_ts = 0.0
        self.half_open_attempts = 0

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_ts = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN


def build_breakers() -> Dict[str, CircuitBreaker]:
    settings = get_settings()
    return {
        "users": CircuitBreaker(
            failure_threshold=settings.cb_failure_threshold,
            open_timeout=settings.cb_open_timeout_seconds,
            half_open_max_calls=settings.cb_half_open_max_calls,
        ),
        "rooms": CircuitBreaker(
            failure_threshold=settings.cb_failure_threshold,
            open_timeout=settings.cb_open_timeout_seconds,
            half_open_max_calls=settings.cb_half_open_max_calls,
        ),
        "bookings": CircuitBreaker(
            failure_threshold=settings.cb_failure_threshold,
            open_timeout=settings.cb_open_timeout_seconds,
            half_open_max_calls=settings.cb_half_open_max_calls,
        ),
        "reviews": CircuitBreaker(
            failure_threshold=settings.cb_failure_threshold,
            open_timeout=settings.cb_open_timeout_seconds,
            half_open_max_calls=settings.cb_half_open_max_calls,
        ),
    }


# Global breaker registry keyed by target service name.
_BREAKERS: Dict[str, CircuitBreaker] = build_breakers()


def get_breaker(service_name: str) -> CircuitBreaker:
    return _BREAKERS[service_name]
