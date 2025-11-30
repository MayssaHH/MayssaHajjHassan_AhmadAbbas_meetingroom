"""
common.notifications
====================

Notification sending functionality for the Smart Meeting Room backend.

This module provides functions to send email notifications via SendGrid
for booking-related events. Notifications are sent asynchronously and
failures do not interrupt the main business flow.
"""

from __future__ import annotations

import logging
from datetime import datetime

import httpx

from common.config import get_settings
from common.exceptions import NotificationError
from common.logging_utils import get_logger

_logger = get_logger(__name__)

SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"


def _is_notifications_configured() -> bool:
    """
    Check if notifications are enabled and properly configured.

    Returns
    -------
    bool
        True if notifications are enabled and SendGrid is configured.
    """
    settings = get_settings()
    
    if not settings.notifications_enabled:
        _logger.debug("Notifications are disabled (NOTIFICATIONS_ENABLED=False)")
        return False
    
    if not settings.sendgrid_api_key:
        _logger.warning("SendGrid not configured: SENDGRID_API_KEY is missing")
        return False
    
    if not settings.sendgrid_from_email:
        _logger.warning("SendGrid not configured: SENDGRID_FROM_EMAIL is missing")
        return False
    
    return True


def _send_email(
    to_email: str,
    subject: str,
    content: str,
) -> None:
    """
    Send an email via SendGrid API.

    Parameters
    ----------
    to_email:
        Recipient email address.
    subject:
        Email subject line.
    content:
        Plain text email content.

    Raises
    ------
    NotificationError
        If the SendGrid API call fails with a non-2xx status code.
    """
    settings = get_settings()
    
    if not _is_notifications_configured():
        return
    
    headers = {
        "Authorization": f"Bearer {settings.sendgrid_api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "from": {
            "email": settings.sendgrid_from_email,
        },
        "personalizations": [
            {
                "to": [
                    {
                        "email": to_email,
                    }
                ],
                "subject": subject,
            }
        ],
        "content": [
            {
                "type": "text/plain",
                "value": content,
            }
        ],
    }
    
    try:
        response = httpx.post(
            SENDGRID_API_URL,
            headers=headers,
            json=payload,
            timeout=10.0,
        )
        
        if response.status_code >= 200 and response.status_code < 300:
            _logger.info(
                "Notification sent successfully to %s: %s",
                to_email,
                subject,
            )
        else:
            error_msg = (
                f"SendGrid API returned {response.status_code}: "
                f"{response.text[:200]}"
            )
            _logger.error(error_msg)
            raise NotificationError(
                message="Failed to send notification email.",
                details={
                    "status_code": response.status_code,
                    "response": response.text[:500],
                },
            )
    
    except httpx.HTTPError as exc:
        _logger.exception("HTTP error while sending notification: %s", exc)
        raise NotificationError(
            message="Network error while sending notification.",
            details={"error": str(exc)},
        ) from exc


def send_booking_created_notification(
    user_email: str,
    room_name: str,
    start_time: datetime,
    end_time: datetime,
) -> None:
    """
    Send a notification email when a booking is created.

    Parameters
    ----------
    user_email:
        Email address of the user who made the booking.
    room_name:
        Name of the booked room.
    start_time:
        Booking start time.
    end_time:
        Booking end time.

    Notes
    -----
    This function logs errors but does not raise exceptions to avoid
    interrupting the booking creation flow. Callers should wrap this
    in try/except if they need to handle notification failures.
    """
    if not _is_notifications_configured():
        return
    
    subject = f"Booking confirmed: {room_name}"
    content = (
        f"Your booking has been confirmed.\n\n"
        f"Room: {room_name}\n"
        f"Start: {start_time.strftime('%Y-%m-%d %H:%M')}\n"
        f"End: {end_time.strftime('%Y-%m-%d %H:%M')}\n"
    )
    
    try:
        _send_email(to_email=user_email, subject=subject, content=content)
    except NotificationError:
        # Log but don't re-raise to avoid breaking booking flow
        _logger.warning(
            "Failed to send booking created notification to %s (booking still created)",
            user_email,
        )
    except Exception as exc:
        # Catch any other unexpected errors
        _logger.exception(
            "Unexpected error sending booking created notification to %s: %s",
            user_email,
            exc,
        )


def send_booking_cancelled_notification(
    user_email: str,
    room_name: str,
    start_time: datetime,
    end_time: datetime,
) -> None:
    """
    Send a notification email when a booking is cancelled.

    Parameters
    ----------
    user_email:
        Email address of the user whose booking was cancelled.
    room_name:
        Name of the cancelled room.
    start_time:
        Original booking start time.
    end_time:
        Original booking end time.

    Notes
    -----
    This function logs errors but does not raise exceptions to avoid
    interrupting the booking cancellation flow. Callers should wrap this
    in try/except if they need to handle notification failures.
    """
    if not _is_notifications_configured():
        return
    
    subject = f"Booking cancelled: {room_name}"
    content = (
        f"Your booking has been cancelled.\n\n"
        f"Room: {room_name}\n"
        f"Original start: {start_time.strftime('%Y-%m-%d %H:%M')}\n"
        f"Original end: {end_time.strftime('%Y-%m-%d %H:%M')}\n"
    )
    
    try:
        _send_email(to_email=user_email, subject=subject, content=content)
    except NotificationError:
        # Log but don't re-raise to avoid breaking booking flow
        _logger.warning(
            "Failed to send booking cancelled notification to %s (booking still cancelled)",
            user_email,
        )
    except Exception as exc:
        # Catch any other unexpected errors
        _logger.exception(
            "Unexpected error sending booking cancelled notification to %s: %s",
            user_email,
            exc,
        )

