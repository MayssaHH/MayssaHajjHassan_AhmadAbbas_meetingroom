"""
Unit tests for the notification helper functions.

These tests verify that notifications are sent correctly via SendGrid
and that the system respects the NOTIFICATIONS_ENABLED configuration.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.notifications import (  # noqa: E402
    send_booking_created_notification,
    send_booking_cancelled_notification,
)


@pytest.fixture
def mock_httpx_post():
    """Create a mock for httpx.post that records calls."""
    with patch("common.notifications.httpx.post") as mock_post:
        # Create a mock response with status_code 202 (accepted)
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.text = "OK"
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def mock_settings_enabled():
    """Mock settings with notifications enabled."""
    with patch("common.notifications.get_settings") as mock_get_settings:
        mock_settings = Mock()
        mock_settings.notifications_enabled = True
        mock_settings.sendgrid_api_key = "test_api_key_12345"
        mock_settings.sendgrid_from_email = "noreply@example.com"
        mock_get_settings.return_value = mock_settings
        yield mock_settings


@pytest.fixture
def mock_settings_disabled():
    """Mock settings with notifications disabled."""
    with patch("common.notifications.get_settings") as mock_get_settings:
        mock_settings = Mock()
        mock_settings.notifications_enabled = False
        mock_settings.sendgrid_api_key = "test_api_key_12345"
        mock_settings.sendgrid_from_email = "noreply@example.com"
        mock_get_settings.return_value = mock_settings
        yield mock_settings


def test_send_booking_created_notification_success(
    mock_httpx_post, mock_settings_enabled
):
    """Test that send_booking_created_notification calls SendGrid API correctly."""
    start_time = datetime(2024, 12, 15, 14, 0, 0, tzinfo=timezone.utc)
    end_time = datetime(2024, 12, 15, 15, 0, 0, tzinfo=timezone.utc)
    
    send_booking_created_notification(
        user_email="test@example.com",
        room_name="Room A",
        start_time=start_time,
        end_time=end_time,
    )
    
    # Assert httpx.post was called once
    assert mock_httpx_post.call_count == 1
    
    # Get the call arguments
    call_args = mock_httpx_post.call_args
    
    # Assert URL is SendGrid endpoint
    assert call_args[0][0] == "https://api.sendgrid.com/v3/mail/send"
    
    # Assert headers contain Authorization and Content-Type
    headers = call_args[1]["headers"]
    assert headers["Authorization"] == "Bearer test_api_key_12345"
    assert headers["Content-Type"] == "application/json"
    
    # Assert JSON payload structure
    payload = call_args[1]["json"]
    assert payload["from"]["email"] == "noreply@example.com"
    assert payload["personalizations"][0]["to"][0]["email"] == "test@example.com"
    assert payload["personalizations"][0]["subject"] == "Booking confirmed: Room A"
    assert payload["content"][0]["type"] == "text/plain"
    assert "Room A" in payload["content"][0]["value"]
    assert "2024-12-15 14:00" in payload["content"][0]["value"]
    assert "2024-12-15 15:00" in payload["content"][0]["value"]
    
    # Assert timeout is set
    assert call_args[1]["timeout"] == 10.0


def test_send_booking_cancelled_notification_success(
    mock_httpx_post, mock_settings_enabled
):
    """Test that send_booking_cancelled_notification calls SendGrid API correctly."""
    start_time = datetime(2024, 12, 15, 14, 0, 0, tzinfo=timezone.utc)
    end_time = datetime(2024, 12, 15, 15, 0, 0, tzinfo=timezone.utc)
    
    send_booking_cancelled_notification(
        user_email="test@example.com",
        room_name="Room B",
        start_time=start_time,
        end_time=end_time,
    )
    
    # Assert httpx.post was called once
    assert mock_httpx_post.call_count == 1
    
    # Get the call arguments
    call_args = mock_httpx_post.call_args
    
    # Assert URL is SendGrid endpoint
    assert call_args[0][0] == "https://api.sendgrid.com/v3/mail/send"
    
    # Assert JSON payload structure
    payload = call_args[1]["json"]
    assert payload["personalizations"][0]["to"][0]["email"] == "test@example.com"
    assert payload["personalizations"][0]["subject"] == "Booking cancelled: Room B"
    assert "Room B" in payload["content"][0]["value"]
    assert "cancelled" in payload["content"][0]["value"].lower()


def test_notifications_disabled_no_api_call(mock_httpx_post, mock_settings_disabled):
    """Test that httpx.post is not called when NOTIFICATIONS_ENABLED is False."""
    start_time = datetime(2024, 12, 15, 14, 0, 0, tzinfo=timezone.utc)
    end_time = datetime(2024, 12, 15, 15, 0, 0, tzinfo=timezone.utc)
    
    send_booking_created_notification(
        user_email="test@example.com",
        room_name="Room A",
        start_time=start_time,
        end_time=end_time,
    )
    
    # Assert httpx.post was NOT called
    assert mock_httpx_post.call_count == 0


def test_notifications_missing_api_key_no_call(mock_httpx_post):
    """Test that httpx.post is not called when API key is missing."""
    with patch("common.notifications.get_settings") as mock_get_settings:
        mock_settings = Mock()
        mock_settings.notifications_enabled = True
        mock_settings.sendgrid_api_key = None  # Missing API key
        mock_settings.sendgrid_from_email = "noreply@example.com"
        mock_get_settings.return_value = mock_settings
        
        start_time = datetime(2024, 12, 15, 14, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 12, 15, 15, 0, 0, tzinfo=timezone.utc)
        
        send_booking_created_notification(
            user_email="test@example.com",
            room_name="Room A",
            start_time=start_time,
            end_time=end_time,
        )
        
        # Assert httpx.post was NOT called
        assert mock_httpx_post.call_count == 0


def test_notifications_missing_from_email_no_call(mock_httpx_post):
    """Test that httpx.post is not called when from email is missing."""
    with patch("common.notifications.get_settings") as mock_get_settings:
        mock_settings = Mock()
        mock_settings.notifications_enabled = True
        mock_settings.sendgrid_api_key = "test_api_key_12345"
        mock_settings.sendgrid_from_email = None  # Missing from email
        mock_get_settings.return_value = mock_settings
        
        start_time = datetime(2024, 12, 15, 14, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 12, 15, 15, 0, 0, tzinfo=timezone.utc)
        
        send_booking_created_notification(
            user_email="test@example.com",
            room_name="Room A",
            start_time=start_time,
            end_time=end_time,
        )
        
        # Assert httpx.post was NOT called
        assert mock_httpx_post.call_count == 0


def test_notification_error_handled_gracefully(mock_httpx_post, mock_settings_enabled):
    """Test that notification errors are handled gracefully and don't raise exceptions."""
    # Make httpx.post raise an exception
    mock_httpx_post.side_effect = Exception("Network error")
    
    start_time = datetime(2024, 12, 15, 14, 0, 0, tzinfo=timezone.utc)
    end_time = datetime(2024, 12, 15, 15, 0, 0, tzinfo=timezone.utc)
    
    # Should not raise an exception
    send_booking_created_notification(
        user_email="test@example.com",
        room_name="Room A",
        start_time=start_time,
        end_time=end_time,
    )
    
    # Assert httpx.post was called (attempted to send)
    assert mock_httpx_post.call_count == 1


def test_notification_non_2xx_status_handled(mock_httpx_post, mock_settings_enabled):
    """Test that non-2xx status codes are handled gracefully."""
    # Create a mock response with error status
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_httpx_post.return_value = mock_response
    
    start_time = datetime(2024, 12, 15, 14, 0, 0, tzinfo=timezone.utc)
    end_time = datetime(2024, 12, 15, 15, 0, 0, tzinfo=timezone.utc)
    
    # Should not raise an exception (caught internally)
    send_booking_created_notification(
        user_email="test@example.com",
        room_name="Room A",
        start_time=start_time,
        end_time=end_time,
    )
    
    # Assert httpx.post was called
    assert mock_httpx_post.call_count == 1

