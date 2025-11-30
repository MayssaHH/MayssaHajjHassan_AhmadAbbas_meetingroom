"""
common.exceptions
=================

Custom exception hierarchy for the Smart Meeting Room backend.

All errors follow a unified JSON response format:
{
    "error_code": "...",
    "message": "...",
    "details": { ... }
}

Using explicit exception classes makes it easier to apply consistent
error handling and to map internal failures to well-structured HTTP
responses in the API layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AppError(Exception):
    """
    Base class for all application errors.

    Each error carries an HTTP status code, machine-friendly error_code,
    human-readable message, and optional details.
    """

    http_status: int
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error to the unified JSON format.

        Returns
        -------
        dict
            Error in the standard format:
            {
                "error_code": "...",
                "message": "...",
                "details": { ... }
            }
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details or {},
        }


class BadRequestError(AppError):
    """
    Raised when the request contains invalid data or parameters.

    HTTP Status: 400
    Error Code: VALIDATION_ERROR (default)
    """

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            http_status=400,
            error_code=error_code,
            message=message,
            details=details,
        )


class UnauthorizedError(AppError):
    """
    Raised when authentication fails or is missing entirely.

    HTTP Status: 401
    Error Code: UNAUTHORIZED
    """

    def __init__(
        self,
        message: str = "Authentication required.",
        *,
        error_code: str = "UNAUTHORIZED",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            http_status=401,
            error_code=error_code,
            message=message,
            details=details,
        )


class ForbiddenError(AppError):
    """
    Raised when the current user is authenticated but lacks permission
    to perform an operation.

    HTTP Status: 403
    Error Code: FORBIDDEN
    """

    def __init__(
        self,
        message: str = "You do not have permission to perform this operation.",
        *,
        error_code: str = "FORBIDDEN",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            http_status=403,
            error_code=error_code,
            message=message,
            details=details,
        )


class NotFoundError(AppError):
    """
    Raised when a requested entity does not exist in the database.

    HTTP Status: 404
    Error Code: NOT_FOUND (default) or more specific like USER_NOT_FOUND
    """

    def __init__(
        self,
        message: str = "Resource not found.",
        *,
        error_code: str = "NOT_FOUND",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            http_status=404,
            error_code=error_code,
            message=message,
            details=details,
        )


class ConflictError(AppError):
    """
    Raised when a requested operation conflicts with existing state.

    Typical use cases include overlapping room bookings or attempts to
    create duplicate resources that must be unique.

    HTTP Status: 409
    Error Code: CONFLICT (default) or more specific like BOOKING_CONFLICT
    """

    def __init__(
        self,
        message: str = "Operation conflicts with existing state.",
        *,
        error_code: str = "CONFLICT",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            http_status=409,
            error_code=error_code,
            message=message,
            details=details,
        )


class InternalServerError(AppError):
    """
    Raised for unexpected internal server errors.

    HTTP Status: 500
    Error Code: INTERNAL_ERROR
    """

    def __init__(
        self,
        message: str = "An unexpected error occurred.",
        *,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            http_status=500,
            error_code="INTERNAL_ERROR",
            message=message,
            details=details,
        )


class CircuitOpenError(AppError):
    """
    Raised when a circuit breaker is open and downstream service is unavailable.

    HTTP Status: 503
    Error Code: CIRCUIT_OPEN
    """

    def __init__(
        self,
        message: str = "Circuit is open; downstream unavailable.",
        *,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            http_status=503,
            error_code="CIRCUIT_OPEN",
            message=message,
            details=details,
        )


class DownstreamServiceError(AppError):
    """
    Raised when a downstream service returns an error.

    HTTP Status: 502
    Error Code: DOWNSTREAM_ERROR
    """

    def __init__(
        self,
        message: str = "Downstream service error.",
        *,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            http_status=502,
            error_code="DOWNSTREAM_ERROR",
            message=message,
            details=details,
        )


class RateLimitExceededError(AppError):
    """
    Raised when rate limit is exceeded.

    HTTP Status: 429
    Error Code: RATE_LIMIT_EXCEEDED
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded.",
        *,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            http_status=429,
            error_code="RATE_LIMIT_EXCEEDED",
            message=message,
            details=details,
        )


class NotificationError(AppError):
    """
    Raised when notification delivery fails.

    HTTP Status: 502
    Error Code: NOTIFICATION_FAILED
    """

    def __init__(
        self,
        message: str = "Notification delivery failed.",
        *,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            http_status=502,
            error_code="NOTIFICATION_FAILED",
            message=message,
            details=details,
        )
