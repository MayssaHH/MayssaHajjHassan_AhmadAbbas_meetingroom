"""
common.exceptions
=================

Custom exception hierarchy for the Smart Meeting Room backend.

Using explicit exception classes makes it easier to apply consistent
error handling and to map internal failures to well-structured HTTP
responses in the API layer.
"""

from __future__ import annotations


class AppError(Exception):
    """
    Base class for all custom application errors.

    Subclasses represent specific failure modes that will later be
    translated into explicit HTTP error responses by the API layer.
    """


class NotFoundError(AppError):
    """
    Raised when a requested entity does not exist in the database.
    """


class ConflictError(AppError):
    """
    Raised when a requested operation conflicts with existing state.

    Typical use cases include overlapping room bookings or attempts to
    create duplicate resources that must be unique.
    """


class UnauthorizedError(AppError):
    """
    Raised when authentication fails or is missing entirely.
    """


class ForbiddenError(AppError):
    """
    Raised when the current user is authenticated but lacks permission
    to perform an operation.
    """
