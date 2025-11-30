"""
Administrator-specific routes for the Users service.

This router covers administrative operations such as:

* Changing another user's role.
* Deleting arbitrary user accounts.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from common.rbac import ROLE_ADMIN
from common.exceptions import NotFoundError, BadRequestError
from db.schema import User
from services.users.app.dependencies import get_db, require_roles
from services.users.app.schemas import RoleLiteral
from services.users.app.repository import user_repository
from services.users.app.service_layer import user_service
from services.users.app.clients import bookings_client


router = APIRouter()


class RoleUpdatePayload(BaseModel):
    """
    Pydantic model describing the payload for role updates.
    """

    role: RoleLiteral


@router.patch("/{user_id}/role", status_code=status.HTTP_200_OK)
@router.put("/{user_id}/role", status_code=status.HTTP_200_OK)
def update_user_role(
    user_id: int,
    payload: RoleUpdatePayload,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles([ROLE_ADMIN])),
):
    """
    Update the role of a user identified by ``user_id``.
    """
    user = user_repository.get_user_by_id(db, user_id)
    if user is None:
        raise NotFoundError("User not found.", error_code="USER_NOT_FOUND")

    try:
        normalized_role = user_service.normalize_role(payload.role)
    except ValueError as exc:
        raise BadRequestError(str(exc)) from exc

    if user.id == current_admin.id and normalized_role != ROLE_ADMIN:
        raise BadRequestError("Admins cannot demote themselves.")

    user.role = normalized_role
    user_repository.save_user(db, user)
    return {"id": user.id, "role": user.role}


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_as_admin(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles([ROLE_ADMIN])),
):
    """
    Delete a user account by its primary key.

    This operation is restricted to administrators.
    """
    user = user_repository.get_user_by_id(db, user_id)
    if user is None:
        raise NotFoundError("User not found.", error_code="USER_NOT_FOUND")

    user_repository.delete_user(db, user)
    return None


@router.get("/{user_id}/bookings", status_code=status.HTTP_200_OK)
def get_user_booking_history(
    user_id: int,
    _: User = Depends(require_roles([ROLE_ADMIN])),
):
    """
    Admin-only: view a user's booking history via Bookings service.
    """
    return bookings_client.fetch_user_bookings(user_id)


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    user_id: int,
    new_password: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles([ROLE_ADMIN])),
):
    """
    Admin-only password reset for a user.
    """
    user = user_repository.get_user_by_id(db, user_id)
    if user is None:
        raise NotFoundError("User not found.", error_code="USER_NOT_FOUND")
    user_service.change_password(db, user, new_password)
    return None
