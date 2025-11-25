"""
Pydantic schema definitions for the Users service.

These models define the request and response shapes for the Users API,
decoupling external representations from internal database models.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """
    Base user fields that are common across multiple API models.
    """

    username: str = Field(..., description="Unique username of the user.")
    email: EmailStr = Field(..., description="Unique email address of the user.")


class UserCreate(UserBase):
    """
    Schema used when registering a new user.

    In this design, new users are always created with the ``'regular'`` role.
    Role changes are handled by administrator endpoints.
    """

    password: str = Field(..., min_length=6, description="Plaintext password.")


class UserUpdate(BaseModel):
    """
    Schema for updating a user's own profile information.

    All fields are optional to allow partial updates.
    """

    username: Optional[str] = Field(
        None, description="New username to update to, if provided."
    )
    email: Optional[EmailStr] = Field(
        None, description="New email address to update to, if provided."
    )


class UserRead(UserBase):
    """
    Schema returned when reading user information.

    It extends :class:`UserBase` with read-only metadata.
    """

    id: int = Field(..., description="Database identifier of the user.")
    role: str = Field(..., description="Role of the user.")
    created_at: datetime = Field(..., description="Timestamp when the user was created.")

    class Config:
        """
        Pydantic configuration for ORM compatibility.
        """

        from_attributes = True


class TokenResponse(BaseModel):
    """
    Schema returned after a successful authentication.

    It contains the access token and its type (e.g., ``'bearer'``).
    """

    access_token: str = Field(..., description="JWT access token.")
    token_type: str = Field(
        default="bearer",
        description="Authentication scheme of the token (usually 'bearer').",
    )


class UserLogin(BaseModel):
    """
    Request schema used when a user attempts to log in.
    """

    username: str = Field(..., description="Username used to authenticate.")
    password: str = Field(..., description="Plaintext password used to authenticate.")
