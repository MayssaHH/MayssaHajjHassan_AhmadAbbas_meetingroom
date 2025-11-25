"""
User management routes for the Users service.

This router will handle operations such as:

* Listing users (for privileged roles).
* Retrieving a specific user by username.
* Updating and deleting the current user's profile.

The actual route implementations will be added in a later commit.
"""

from fastapi import APIRouter

router = APIRouter()
