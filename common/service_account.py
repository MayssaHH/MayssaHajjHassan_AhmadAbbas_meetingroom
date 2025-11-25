"""
Service account management for inter-service communication.

The project specification defines a *service account* role that is used by
non-human clients (i.e., other microservices) to call protected APIs with
the least privilege required. :contentReference[oaicite:6]{index=6}  

This module will be responsible for:

* Logging in to the Users service using service account credentials.
* Caching the resulting JWT access token in memory.
* Refreshing the token when it is about to expire.
* Providing helper functions that other services can use to attach the
  service account token to outgoing HTTP requests.
"""

from typing import Optional


_SERVICE_ACCOUNT_TOKEN: Optional[str] = None


def get_service_account_token() -> str:
    """
    Return the current service account JWT token.

    Returns
    -------
    str
        The service account access token as a string.

    Notes
    -----
    In future commits this function will:

    * Detect when the token is missing or expired.
    * Perform a login request to the Users service using the configured
      service account username and password.
    * Cache the token in the private module-level variable
      ``_SERVICE_ACCOUNT_TOKEN``.
    """
    if _SERVICE_ACCOUNT_TOKEN is None:
        
        raise RuntimeError(
            "Service account token is not initialized yet. "
            "Implementation will be provided in a later commit."
        )
    return _SERVICE_ACCOUNT_TOKEN
