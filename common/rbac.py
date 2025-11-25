"""
Role-based access control (RBAC) utilities.

This module defines the different user roles and small helper functions
that make authorization checks easier across the microservices.

The roles are aligned with the project specification:

- Admin
- Regular user
- Facility manager
- Moderator
- Auditor (read-only)
- Service account (non-human account for inter-service calls) :contentReference[oaicite:5]{index=5}  
"""

from typing import Iterable


#: System administrator, full permissions.
ROLE_ADMIN: str = "admin"

#: Regular user of the system.
ROLE_REGULAR: str = "regular"

#: Power user for room and inventory management.
ROLE_FACILITY_MANAGER: str = "facility_manager"

#: Lightweight review moderator.
ROLE_MODERATOR: str = "moderator"

#: Read-only user, used mainly for auditing.
ROLE_AUDITOR: str = "auditor"

#: Technical account used for inter-service API calls.
ROLE_SERVICE_ACCOUNT: str = "service_account"


def is_role_allowed(user_role: str, allowed_roles: Iterable[str]) -> bool:
    """
    Check if a given role is allowed to access a protected resource.

    Parameters
    ----------
    user_role:
        The role of the current user (e.g., ``"admin"`` or ``"regular"``).
    allowed_roles:
        An iterable of roles that are allowed to perform the operation.

    Returns
    -------
    bool
        ``True`` if ``user_role`` is contained in ``allowed_roles``,
        otherwise ``False``.
    """
    return user_role in allowed_roles


def has_role(user_role: str, allowed_roles: Iterable[str]) -> bool:
    """
    Alias for :func:`is_role_allowed` kept for backward compatibility.

    Some services import ``has_role`` instead of ``is_role_allowed``.
    """

    return is_role_allowed(user_role, allowed_roles)
