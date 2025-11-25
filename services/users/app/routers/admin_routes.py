"""
Administrator-specific routes for the Users service.

This router will cover administrative operations such as:

* Changing another user's role.
* Deleting arbitrary user accounts.
* Viewing any user's booking history by calling the Bookings service.

The concrete endpoints will be implemented in a later commit.
"""

from fastapi import APIRouter

router = APIRouter()
