"""
Pytest fixtures for the Users service.

This module configures an isolated SQLite database and a reusable
FastAPI :class:`~fastapi.testclient.TestClient` so that endpoint tests
can run without depending on the real development database.
"""

from __future__ import annotations

from typing import Generator
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure the repository root is importable when tests run from anywhere.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.schema import Base
from services.users.app.main import app
from services.users.app import dependencies


# SQLite database that exists only for tests.
TEST_DATABASE_URL = "sqlite:///./test_users.db"

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
    """
    Yield a database session bound to the test engine.

    This function is used as a dependency override for
    :func:`services.users.app.dependencies.get_db`.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply the dependency override once for the whole test session.
app.dependency_overrides[dependencies.get_db] = _override_get_db


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    """
    Reset the SQLite schema before every test function.

    Dropping and recreating the tables ensures that each test starts
    with a clean database state.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Provide a FastAPI :class:`TestClient` instance.

    Tests can depend on this fixture to exercise the API endpoints.
    """
    with TestClient(app) as test_client:
        yield test_client
