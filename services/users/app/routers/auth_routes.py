"""
Authentication-related routes for the Users service.

This router exposes endpoints for:

* User registration.
* User login.
* Retrieving information about the current authenticated user.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.schema import User
from services.users.app import schemas
from services.users.app.dependencies import get_current_user, get_db
from services.users.app.service_layer import user_service

router = APIRouter()


@router.post("/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new user account.

    Returns
    -------
    UserRead
        The created user (without password).
    """
    user: User = user_service.register_user(
        db,
        name=payload.name,
        username=payload.username,
        email=payload.email,
        password=payload.password,
        role=payload.role,
    )
    return user


@router.post("/login", response_model=schemas.TokenResponse)
def login_user(
    payload: schemas.UserLogin,
    db: Session = Depends(get_db),
):
    """
    Authenticate a user and issue an access token.

    Returns
    -------
    TokenResponse
        A JWT access token and token type.
    """
    user = user_service.authenticate_user(
        db,
        username=payload.username,
        password=payload.password,
    )

    token = user_service.create_user_access_token(user)
    return schemas.TokenResponse(access_token=token, token_type="bearer")


@router.get("/me", response_model=schemas.UserRead)
def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Retrieve the profile of the current authenticated user.
    """
    return current_user
