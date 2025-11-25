"""
Database engine and session management utilities.

This module centralizes the SQLAlchemy engine creation so that both the
application code and one-off scripts (such as schema initialization) can
share the exact same configuration.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from common.config import get_settings
from db.schema import Base

settings = get_settings()

# Some SQLite clients require this flag; it's ignored for PostgreSQL.
CONNECT_ARGS = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=CONNECT_ARGS, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """
    Yield a database session for FastAPI dependencies.

    The session is closed automatically once the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
