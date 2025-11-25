"""
common.http_client
==================

Thin wrapper around :mod:`httpx` for inter-service HTTP communication.

Each microservice will construct one or more :class:`ServiceHTTPClient`
instances, configured with the appropriate base URL and service account
credentials, in order to call other services in a consistent and
observable way.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx


class ServiceHTTPClient:
    """
    Simple HTTP client used for inter-service calls.

    Parameters
    ----------
    base_url:
        Base URL of the target service, e.g. ``"http://users-service:8001"``.
    timeout:
        Request timeout in seconds.
    default_headers:
        Optional mapping of headers to include with every request
        (e.g. service-account authorization).
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 5.0,
        default_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.default_headers: Dict[str, str] = default_headers or {}

    def _build_client(self) -> httpx.Client:
        """
        Build a new :class:`httpx.Client` instance.

        The client is created on demand to keep this wrapper very simple.
        Future commits may optimize this to reuse a shared connection
        pool if required.
        """
        return httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def get(self, path: str, headers: Optional[Dict[str, str]] = None, **kwargs: Any) -> httpx.Response:
        """
        Perform a ``GET`` request against the target service.

        Parameters
        ----------
        path:
            Path relative to the configured base URL.
        headers:
            Optional per-request headers.

        Returns
        -------
        httpx.Response
            Low-level HTTP response object.
        """
        merged_headers = {**self.default_headers, **(headers or {})}
        with self._build_client() as client:
            return client.get(path, headers=merged_headers, **kwargs)

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Perform a ``POST`` request against the target service.
        """
        merged_headers = {**self.default_headers, **(headers or {})}
        with self._build_client() as client:
            return client.post(path, json=json, headers=merged_headers, **kwargs)
