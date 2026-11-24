"""Application logging for qauto_mcp (tools + HTTP calls to QAuto), with secret masking.

Named logging_setup, not logging, so it does not shadow the stdlib module.
MCPServer.__init__ calls logging.basicConfig (stderr), so call configure() after it.
stderr is safe for both stdio and Streamable HTTP.
"""

import json
import logging
from typing import Any

from qauto_mcp.config import settings

ROOT_LOGGER = "qauto_mcp"
MASK = "***"
SECRET_KEYS = frozenset(
    {
        "password",
        "repeatpassword",
        "sid",
        "cookie",
        "set-cookie",
        "authorization",
        "qauto_password",
        "x-qauto-password",
    }
)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def configure() -> None:
    logging.getLogger(ROOT_LOGGER).setLevel(settings.log_level)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: MASK if str(k).lower() in SECRET_KEYS else _redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value


def _truncate(text: str) -> str:
    limit = settings.log_body_max_chars
    if len(text) <= limit:
        return text
    return f"{text[:limit]}… [{len(text) - limit} more chars]"


def redact_mapping(data: dict[str, Any]) -> dict[str, Any]:
    """Mask secret keys in tool arguments (recursively)."""
    return _redact(data)


def redact_body(raw: bytes) -> str:
    """JSON → mask secret keys recursively → truncate to LOG_BODY_MAX_CHARS."""
    if not raw:
        return ""
    try:
        text = json.dumps(_redact(json.loads(raw)), ensure_ascii=False)
    except ValueError:
        text = raw.decode("utf-8", errors="replace")
    return _truncate(text)
