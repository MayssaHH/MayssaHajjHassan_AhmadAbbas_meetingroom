"""
Pytest fixtures for the Rooms service.

This module provides:

* A dedicated SQLite test database.
* A dependency override for ``get_db``.
* A reusable :class:`fastapi.testclient.TestClient` instance.
"""

from __future__ import annotations

from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.schema import Base
from services.rooms.app.main import app
from services.rooms.app import dependencies

TEST_DATABASE_URL = "sqlite:///./test_rooms.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply the dependency override once for all tests in this package.
app.dependency_overrides[dependencies.get_db] = _override_get_db


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    """
    Recreate the database schema before each test function.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Provide a FastAPI test client bound to the Rooms app.
    """
    with TestClient(app) as test_client:
        yield test_client
