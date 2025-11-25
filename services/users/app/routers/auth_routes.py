"""
Authentication-related routes for the Users service.

This router will expose endpoints for:

* User registration.
* User login.
* Retrieving information about the current authenticated user (``/users/me``).

The concrete implementations will be added in a later commit.
"""

from fastapi import APIRouter

router = APIRouter()
