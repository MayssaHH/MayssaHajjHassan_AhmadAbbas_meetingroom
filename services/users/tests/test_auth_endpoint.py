"""
Smoke tests for authentication-related endpoints of the Users service.

At this stage, the tests only verify that the FastAPI application and
routers can be imported without errors. Real HTTP tests will be added
once the endpoints are implemented in later commits.
"""

from services.users.app.main import app  # type: ignore[import]  # noqa: F401


def test_users_app_imports() -> None:
    """
    Ensure that the Users service FastAPI application can be imported.

    This acts as a minimal smoke test for the current skeleton structure.
    """
    assert app is not None
