"""
Authentication-related routes for the Users service.

This router exposes endpoints for:

* User registration.
* User login.
* Retrieving information about the current authenticated user.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from common.exceptions import RateLimitExceededError
from db.schema import User
from services.users.app import schemas
from services.users.app.dependencies import get_current_user, get_db, rate_limit_by_ip
from services.users.app.service_layer import user_service

router = APIRouter()


@router.post("/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
    _limit = Depends(rate_limit_by_ip("register")),
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
    _limit = Depends(rate_limit_by_ip("login")),
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


# Simple counter for rate limiting test endpoint
_rate_limit_counter: dict[str, int] = {}
_RATE_LIMIT_THRESHOLD = 3


@router.get("/test-rate-limit")
def test_rate_limit(request: Request):
    """
    Test endpoint that raises RateLimitExceededError after N calls.
    
    This is a dummy endpoint for testing Part-II error types.
    Uses IP address to track calls per client.
    """
    client_ip = request.client.host if request.client else "unknown"
    
    if client_ip not in _rate_limit_counter:
        _rate_limit_counter[client_ip] = 0
    
    _rate_limit_counter[client_ip] += 1
    
    if _rate_limit_counter[client_ip] > _RATE_LIMIT_THRESHOLD:
        raise RateLimitExceededError(
            message="Rate limit exceeded for test endpoint.",
            details={"calls_made": _rate_limit_counter[client_ip], "threshold": _RATE_LIMIT_THRESHOLD}
        )
    
    return {"status": "ok", "calls_made": _rate_limit_counter[client_ip]}
