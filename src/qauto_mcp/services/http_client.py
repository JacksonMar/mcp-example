"""Shared httpx client. The server lifespan opens it on start and closes it on stop.

Its cookie jar keeps the `sid` session cookie after signup or signin.
Event hooks log every outgoing request to QAuto (bodies only on DEBUG, secrets masked).
"""

from typing import Any

import httpx

from qauto_mcp.config import settings
from qauto_mcp.formatting import api_error
from qauto_mcp.logging_setup import get_logger, redact_body

logger = get_logger(__name__)

_client: httpx.AsyncClient | None = None


async def _log_request(request: httpx.Request) -> None:
    logger.info("→ %s %s", request.method, request.url)
    if settings.log_http_bodies and request.content:
        logger.debug("→ body %s", redact_body(request.content))


async def _log_response(response: httpx.Response) -> None:
    await response.aread()  # without it .content and .elapsed are not available in the hook
    logger.info(
        "← %s %s %s (%.0f ms)",
        response.status_code,
        response.request.method,
        response.request.url,
        response.elapsed.total_seconds() * 1000,
    )
    if settings.log_http_bodies:
        logger.debug("← body %s", redact_body(response.content))


def open_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=settings.base_url,
            timeout=settings.timeout,
            event_hooks={"request": [_log_request], "response": [_log_response]},
        )
    return _client


async def close_client() -> None:
    global _client
    if _client is None:
        return
    await _client.aclose()
    _client = None


def get_client() -> httpx.AsyncClient:
    if _client is None:
        raise RuntimeError("HTTP client is not open. The server lifespan must call open_client().")
    return _client


async def call_api(method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
    response = await get_client().request(method, path, json=payload)
    try:
        body = response.json()
    except ValueError:
        body = response.text
    if response.is_error:
        raise api_error(response.status_code, body)
    return body
