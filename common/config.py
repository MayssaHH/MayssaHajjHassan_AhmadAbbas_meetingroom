"""
common.config
=============

Central configuration management for the Smart Meeting Room backend.

The :class:`Settings` object defined here is imported by individual
services to access environment-driven configuration in a consistent way.
Settings are loaded from process environment variables and an optional
``.env`` file.
"""

from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application configuration model.

    All attributes have sensible defaults for local development. For
    production deployments, override them via environment variables or a
    ``.env`` file placed in the project root.

    Attributes
    ----------
    database_url:
        SQLAlchemy connection string used by services when they need to
        talk directly to the shared relational database.
    jwt_secret_key:
        Secret key used to sign JSON Web Tokens.
    jwt_algorithm:
        Algorithm identifier used to sign/verify JWTs.
    access_token_expire_minutes:
        Access token lifetime expressed in minutes.
    users_service_url, rooms_service_url, bookings_service_url,
    reviews_service_url:
        Base URLs used by services when talking to each other over HTTP.
    service_account_username, service_account_password:
        Credentials for the dedicated ``service_account`` user that will
        be used for inter-service calls.
    """

    database_url: str = "postgresql://postgres:postgres@db:5432/smart_meeting_room"
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    users_service_url: str = "http://users-service:8001"
    rooms_service_url: str = "http://rooms-service:8002"
    bookings_service_url: str = "http://bookings-service:8003"
    reviews_service_url: str = "http://reviews-service:8004"

    service_account_username: str = "service_account"
    service_account_password: str = "CHANGE_ME_IN_PRODUCTION"

    class Config:
        """
        Pydantic configuration for :class:`Settings`.

        The project uses a ``.env`` file in the repository root during
        development to avoid hardcoding secrets in the code base.
        """

        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached instance of :class:`Settings`.

    Returns
    -------
    Settings
        The singleton settings instance.
    """
    return Settings()
