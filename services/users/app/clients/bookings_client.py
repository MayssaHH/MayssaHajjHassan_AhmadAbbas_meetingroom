"""
Client utilities for interacting with the Bookings service.

The Users service will use this client to fetch booking history for a given
user when an administrator requests it.

The actual HTTP calls will be implemented in a later commit using the
shared HTTP client utilities from :mod:`common.http_client`.
"""

from typing import Any, Dict, List


def fetch_user_bookings(user_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve the booking history for a specific user from the Bookings service.

    Parameters
    ----------
    user_id:
        The identifier of the user whose bookings are requested.

    Returns
    -------
    list of dict
        A list of booking records associated with the user.

    Notes
    -----
    The implementation will:

    * Obtain a service account token from :mod:`common.service_account`.
    * Perform an HTTP request to the Bookings service.
    * Map the response into a Python-friendly structure.
    """
    raise NotImplementedError("fetch_user_bookings is not implemented yet.")
