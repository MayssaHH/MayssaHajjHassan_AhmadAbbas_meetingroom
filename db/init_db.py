"""
Database engine and session management.

This module creates the SQLAlchemy engine and session factory based on the
configured database URL. It also exposes a :func:`get_db` dependency that
can be used in FastAPI routes.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from common.config import get_settings
from db.schema import Base

settings = get_settings()

# For SQLite, ``check_same_thread`` is required in some environments.
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """
    Create all database tables if they do not already exist.
    """
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """
    FastAPI dependency that yields a database session.

    Yields
    ------
    Session
        A SQLAlchemy session tied to the current request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
