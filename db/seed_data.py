"""
db.seed_data
============

Optional helpers for inserting demonstration or test data into the
database.

During development you may call the functions in this module from
interactive sessions or dedicated scripts to populate the schema with
some sample users, rooms, bookings and reviews.

The functions are intentionally kept minimal in Commit 1 and will be
expanded only if needed later in the project.
"""

from __future__ import annotations

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .schema import Booking, Review, Room, User


def seed_demo_data(engine: Engine) -> None:
    """
    Insert a very small set of demo records.

    This function is a placeholder for future development. It is safe to
    call multiple times in a disposable development database, but it is
    **not** intended for production environments.

    Parameters
    ----------
    engine:
        A live SQLAlchemy :class:`~sqlalchemy.engine.Engine` pointing to
        the target database.
    """
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with SessionLocal() as session:  # type: Session
        # For Commit 1 we do not actually insert rows. The body is left
        # as a stub so that future commits can easily extend it.
        # Example of future logic:
        #   - create default admin user
        #   - create some example rooms
        #   - create example bookings / reviews
        _ = (User, Room, Booking, Review)  # keep linters happy
        session.rollback()
