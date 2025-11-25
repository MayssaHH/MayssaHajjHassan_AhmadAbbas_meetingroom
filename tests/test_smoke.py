"""
Minimal smoke test module.

Real tests will be added in later commits. This file simply verifies
that the core packages can be imported without raising exceptions.
"""


def test_imports() -> None:
    """
    Import a few core modules to ensure they exist.
    """
    import db.schema  # noqa: F401
    import common.config  # noqa: F401
