"""
Authentication and token-related helpers.

This module will centralize all logic related to:

* Password hashing and verification.
* JSON Web Token (JWT) creation and validation.
* Extracting the authenticated user identity and role from a token.

The functions are intentionally left as stubs in the first commit and will
be fully implemented in later commits when the Users service is developed.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any


from jose import JWTError, jwt
from passlib.context import CryptContext

from common.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(
    payload: Optional[Dict[str, Any]] = None,
    *,
    subject: Optional[str] = None,
    role: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token for a given subject and role.

    Parameters
    ----------
    payload:
        Optional dictionary of claims to encode directly into the token.
        If omitted, ``subject`` and ``role`` must be provided.
    subject:
        Convenience parameter to populate/override the ``sub`` claim.
    role:
        Convenience parameter to populate/override the ``role`` claim.
    expires_delta:
        Optional lifetime for the token as a :class:`datetime.timedelta`.

    Returns
    -------
    str
        The encoded JWT token as a string.

    Notes
    -----
    The concrete signing algorithm, secret key, and claim layout will be
    added in a later commit once configuration and the Users service are in place.
    """
    
    settings = get_settings()
    claims: Dict[str, Any] = {}
    if payload:
        claims.update(payload)

    if subject is not None:
        claims["sub"] = subject
    if role is not None:
        claims["role"] = role

    if "sub" not in claims or "role" not in claims:
        raise ValueError("Both 'sub' and 'role' claims are required to create an access token.")

    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    expire = datetime.utcnow() + expires_delta
    claims["sub"] = str(claims["sub"])
    claims["role"] = str(claims["role"])
    claims["exp"] = expire

    encoded_jwt = jwt.encode(
        claims,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def verify_access_token(token: str) -> dict:
    """
    Verify a JWT access token and return its decoded payload.

    Parameters
    ----------
    token:
        The raw JWT access token as received in the ``Authorization`` header.

    Returns
    -------
    dict
        The decoded token payload as a dictionary.

    Raises
    ------
    RuntimeError
        If the token is invalid, expired, or cannot be decoded.

    Notes
    -----
    The concrete verification logic (secret key, algorithm, and error
    handling strategy) will be implemented in a later commit.
    """
    
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as exc:  # pragma: no cover - defensive
        raise RuntimeError("Invalid or expired token") from exc


def decode_access_token(token: str) -> dict:
    """
    Backwards-compatible alias for :func:`verify_access_token`.

    Some services still import ``decode_access_token``; keep this thin
    wrapper so that those imports continue to work without modification.
    """

    return verify_access_token(token)


def get_password_hash(plain_password: str) -> str:
    """
    Compute a secure hash for a plaintext password.

    Parameters
    ----------
    plain_password:
        The plaintext password provided by the user.

    Returns
    -------
    str
        A salted and hashed representation of the password.

    Notes
    -----
    The concrete hashing algorithm (e.g., bcrypt) will be chosen and wired
    in a later commit.
    """
    
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify that a plaintext password matches a stored hash.

    Parameters
    ----------
    plain_password:
        The plaintext password entered by the user.
    hashed_password:
        The hashed password retrieved from persistent storage.

    Returns
    -------
    bool
        ``True`` if the password matches the hash, otherwise ``False``.
    """
    
    return _pwd_context.verify(plain_password, hashed_password)
