"""
db.init_db
==========

Database initialization helpers.

This module provides small utility functions that will later be used by
CLI scripts or service startup hooks to create the database schema.

At this stage it only exposes utilities to create all tables defined in
:mod:`db.schema`.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from .schema import Base


def create_engine_for_url(database_url: str) -> Engine:
    """
    Build a SQLAlchemy :class:`~sqlalchemy.engine.Engine` for the given URL.

    Parameters
    ----------
    database_url:
        Full SQLAlchemy connection string, e.g.
        ``postgresql://user:password@host:5432/dbname``.

    Returns
    -------
    Engine
        Configured SQLAlchemy engine instance.
    """
    return create_engine(database_url, future=True)


def init_db(database_url: str) -> None:
    """
    Create all database tables defined in :mod:`db.schema`.

    This helper is intentionally small and synchronous so that it can be
    reused from service startup code or from one-off migration scripts.

    Parameters
    ----------
    database_url:
        Database connection string for the target database.
    """
    engine = create_engine_for_url(database_url)
    Base.metadata.create_all(bind=engine)
