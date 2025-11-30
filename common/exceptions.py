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

from typing import Any, Dict, Optional


class AppError(Exception):
    """
    Base class for all custom application errors.

    All application errors follow a unified format with:
    - error_code: Machine-readable error identifier (UPPER_SNAKE_CASE)
    - message: Human-readable error message
    - details: Optional dictionary with contextual information
    - http_status: HTTP status code to return

    Subclasses represent specific failure modes that will be
    translated into explicit HTTP error responses by the API layer.
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        http_status: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize an application error.

        Parameters
        ----------
        message:
            Human-readable error message.
        error_code:
            Machine-readable error identifier (e.g., "VALIDATION_ERROR").
        http_status:
            HTTP status code to return (default: 500).
        details:
            Optional dictionary with contextual information about the error.
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.http_status = http_status
        self.details = details or {}

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
            "details": self.details if self.details else {},
        }


class BadRequestError(AppError):
    """
    Raised when the request contains invalid data or parameters.

    HTTP Status: 400
    Error Code: VALIDATION_ERROR (or more specific codes)
    """

    def __init__(
        self,
        message: str,
        error_code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            http_status=400,
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
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="UNAUTHORIZED",
            http_status=401,
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
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="FORBIDDEN",
            http_status=403,
            details=details,
        )


class NotFoundError(AppError):
    """
    Raised when a requested entity does not exist in the database.

    HTTP Status: 404
    Error Code: NOT_FOUND (or more specific like USER_NOT_FOUND)
    """

    def __init__(
        self,
        message: str,
        error_code: str = "NOT_FOUND",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            http_status=404,
            details=details,
        )


class ConflictError(AppError):
    """
    Raised when a requested operation conflicts with existing state.

    Typical use cases include overlapping room bookings or attempts to
    create duplicate resources that must be unique.

    HTTP Status: 409
    Error Code: CONFLICT (or more specific like BOOKING_CONFLICT)
    """

    def __init__(
        self,
        message: str,
        error_code: str = "CONFLICT",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            http_status=409,
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
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="INTERNAL_ERROR",
            http_status=500,
            details=details,
        )
