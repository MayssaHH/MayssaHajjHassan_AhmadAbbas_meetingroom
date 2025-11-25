"""
Administrator-specific routes for the Users service.

This router covers administrative operations such as:

* Changing another user's role.
* Deleting arbitrary user accounts.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from common.rbac import ROLE_ADMIN
from db.schema import User
from services.users.app.dependencies import get_db, require_roles
from services.users.app.schemas import RoleLiteral
from services.users.app.repository import user_repository
from services.users.app.service_layer import user_service


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
    _: User = Depends(require_roles([ROLE_ADMIN])),
):
    """
    Update the role of a user identified by ``user_id``.
    """
    user = user_repository.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    try:
        normalized_role = user_service.normalize_role(payload.role)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    user_repository.delete_user(db, user)
    return None
