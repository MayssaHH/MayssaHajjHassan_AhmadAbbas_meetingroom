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
import time
from httpx import TimeoutException, HTTPError, Response

import httpx

from common.config import get_settings
from common.circuit_breaker import get_breaker
from common.exceptions import DownstreamServiceError, CircuitOpenError


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
        service_name: Optional[str] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.default_headers: Dict[str, str] = default_headers or {}
        self.service_name = service_name or "downstream"

    def _build_client(self) -> httpx.Client:
        """
        Build a new :class:`httpx.Client` instance.

        The client is created on demand to keep this wrapper very simple.
        Future commits may optimize this to reuse a shared connection
        pool if required.
        """
        return httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def _do_with_retries(self, method: str, path: str, *, headers: Dict[str, str], **kwargs: Any) -> httpx.Response:
        """
        Execute a request with basic retry/backoff on network errors.
        """
        settings = get_settings()
        retries = max(settings.http_client_retries, 0)
        attempt = 0
        backoff = 0.25
        last_exc: Optional[Exception] = None

        while attempt <= retries:
            try:
                with self._build_client() as client:
                    breaker = get_breaker(self.service_name)
                    if settings.cb_enabled:
                        breaker.before_call()
                    resp: Response = client.request(method, path, headers=headers, **kwargs)
                    if resp.status_code >= 500:
                        if settings.cb_enabled:
                            breaker.record_failure()
                        resp.raise_for_status()
                    if settings.cb_enabled:
                        breaker.record_success()
                    return resp
            except (TimeoutException, HTTPError) as exc:
                last_exc = exc
                attempt += 1
                if attempt > retries:
                    break
                time.sleep(backoff)
                backoff *= 2
        if last_exc:
            if isinstance(last_exc, CircuitOpenError):
                raise last_exc
            # On repeated failure, open circuit.
            if get_settings().cb_enabled:
                breaker = get_breaker(self.service_name)
                breaker.record_failure()
            raise DownstreamServiceError(str(last_exc))
        raise RuntimeError("HTTP request failed without exception")  # pragma: no cover

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
        return self._do_with_retries("GET", path, headers=merged_headers, **kwargs)

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
        return self._do_with_retries("POST", path, headers=merged_headers, json=json, **kwargs)
