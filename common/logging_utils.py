"""
common.logging_utils
====================

Central logging configuration helpers.

All services should import :func:`get_logger` instead of configuring the
:mod:`logging` module individually. This keeps log formatting and
metadata consistent across the project and simplifies future auditing
and profiling tasks.
"""

from __future__ import annotations

import logging
from typing import Optional


def configure_logging(service_name: str) -> None:
    """
    Configure the root logger for a service.

    This function is intentionally minimal in Commit 1. Later on, it can
    be extended to include structured logging, correlation IDs, or
    integration with external log aggregation tools.

    Parameters
    ----------
    service_name:
        Human-readable name of the microservice using the logger.
    """
    logging.basicConfig(
        level=logging.INFO,
        format=f"%(asctime)s | {service_name} | %(levelname)s | %(name)s | %(message)s",
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a logger instance.

    Parameters
    ----------
    name:
        Optional logger name. If omitted, the root logger is returned.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    return logging.getLogger(name)


def log_error(logger: logging.Logger, *, service_name: str, path: str, method: str, error_code: str, message: str) -> None:
    """
    Lightweight error logger used by global exception handlers.
    """
    logger.error("%s | %s %s | %s | %s", service_name, method, path, error_code, message)
