"""
User management routes for the Users service.

This router handles operations such as:

* Listing users (for privileged roles).
* Retrieving a specific user by username.
* Updating and deleting the current user's profile.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from common.rbac import ROLE_ADMIN, ROLE_AUDITOR
from db.init_db import get_db
from db.schema import User
from services.users.app import schemas
from services.users.app.dependencies import get_current_user, require_roles
from services.users.app.repository import user_repository

router = APIRouter()


@router.get("/", response_model=List[schemas.UserRead])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles([ROLE_ADMIN, ROLE_AUDITOR])),
):
    """
    List all users in the system.

    This endpoint is restricted to administrative or auditing roles.
    """
    users = user_repository.list_all_users(db)
    return users


@router.get("/{username}", response_model=schemas.UserRead)
def get_user_by_username(
    username: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles([ROLE_ADMIN, ROLE_AUDITOR])),
):
    """
    Retrieve a specific user by username.

    Only administrative or auditing roles are allowed to access this endpoint.
    """
    user = user_repository.get_user_by_username(db, username=username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user


@router.put("/me", response_model=schemas.UserRead)
def update_current_user(
    payload: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update the profile of the current authenticated user.
    """
    if payload.username is not None:
        if user_repository.get_user_by_username(db, username=payload.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken.",
            )
        current_user.username = payload.username

    if payload.email is not None:
        if user_repository.get_user_by_email(db, email=payload.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already in use.",
            )
        current_user.email = payload.email

    updated_user = user_repository.save_user(db, current_user)
    return updated_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_current_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete the current authenticated user account.
    """
    user_repository.delete_user(db, current_user)
    return None
