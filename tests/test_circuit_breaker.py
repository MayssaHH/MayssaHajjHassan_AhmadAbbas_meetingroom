import time
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.circuit_breaker import CircuitBreaker, CircuitState  # noqa: E402
from common.exceptions import CircuitOpenError  # noqa: E402


def test_circuit_opens_after_threshold_and_recovers_on_success():
    cb = CircuitBreaker(failure_threshold=2, open_timeout=1, half_open_max_calls=1)
    cb.before_call()
    cb.record_failure()
    cb.before_call()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    with pytest.raises(CircuitOpenError):
        cb.before_call()

    time.sleep(1.05)
    cb.before_call()
    assert cb.state == CircuitState.HALF_OPEN
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_circuit_reopens_if_half_open_probe_fails():
    cb = CircuitBreaker(failure_threshold=1, open_timeout=0, half_open_max_calls=1)
    cb.before_call()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    cb.before_call()  # moves to HALF_OPEN (open_timeout=0)
    assert cb.state == CircuitState.HALF_OPEN
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    # With open_timeout=0, next before_call immediately moves to HALF_OPEN again (no raise)
    cb.before_call()
    assert cb.state == CircuitState.HALF_OPEN
