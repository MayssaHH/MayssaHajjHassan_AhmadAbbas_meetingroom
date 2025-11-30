"""
Test for RateLimitExceededError (Part-II error type).

This test verifies that the rate limiting error returns:
- Status = 429
- error_code = "RATE_LIMIT_EXCEEDED"
- Response JSON has {error_code, message, details} structure.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_rate_limit_exceeded_error(client: TestClient) -> None:
    """
    Test that rate limiting endpoint returns proper error structure.
    """
    # Make calls up to the threshold (should succeed)
    for i in range(3):
        response = client.get("/api/v1/users/test-rate-limit")
        assert response.status_code == 200, f"Call {i+1} should succeed: {response.text}"
        data = response.json()
        assert data["status"] == "ok"
        assert data["calls_made"] == i + 1
    
    # Next call should trigger rate limit error
    response = client.get("/api/v1/users/test-rate-limit")
    
    # Verify status code
    assert response.status_code == 429, f"Expected 429, got {response.status_code}: {response.text}"
    
    # Verify error structure
    data = response.json()
    assert "error_code" in data, f"Missing error_code in response: {data}"
    assert "message" in data, f"Missing message in response: {data}"
    assert "details" in data, f"Missing details in response: {data}"
    
    # Verify error code
    assert data["error_code"] == "RATE_LIMIT_EXCEEDED", f"Expected RATE_LIMIT_EXCEEDED, got {data.get('error_code')}"
    
    # Verify message
    assert "rate limit exceeded" in data["message"].lower(), f"Message should mention rate limit: {data.get('message')}"
    
    # Verify details structure
    assert isinstance(data["details"], dict), f"Details should be a dict, got {type(data.get('details'))}"
    assert "calls_made" in data["details"], f"Details should contain calls_made: {data.get('details')}"
    assert "threshold" in data["details"], f"Details should contain threshold: {data.get('details')}"

