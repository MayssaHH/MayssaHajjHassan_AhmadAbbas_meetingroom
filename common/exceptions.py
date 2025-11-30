"""
common.exceptions
=================

Custom exception hierarchy and helpers for consistent error responses.
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
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details or None,
        }


class BadRequestError(AppError):
    def __init__(self, message: str, *, error_code: str = "VALIDATION_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(http_status=400, error_code=error_code, message=message, details=details)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized", *, error_code: str = "UNAUTHORIZED", details: Optional[Dict[str, Any]] = None):
        super().__init__(http_status=401, error_code=error_code, message=message, details=details)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden", *, error_code: str = "FORBIDDEN", details: Optional[Dict[str, Any]] = None):
        super().__init__(http_status=403, error_code=error_code, message=message, details=details)


class NotFoundError(AppError):
    def __init__(self, message: str = "Not found", *, error_code: str = "NOT_FOUND", details: Optional[Dict[str, Any]] = None):
        super().__init__(http_status=404, error_code=error_code, message=message, details=details)


class ConflictError(AppError):
    def __init__(self, message: str = "Conflict", *, error_code: str = "CONFLICT", details: Optional[Dict[str, Any]] = None):
        super().__init__(http_status=409, error_code=error_code, message=message, details=details)


class InternalServerError(AppError):
    def __init__(self, message: str = "An unexpected error occurred.", *, details: Optional[Dict[str, Any]] = None):
        super().__init__(http_status=500, error_code="INTERNAL_ERROR", message=message, details=details)
