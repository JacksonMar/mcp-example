"""All server settings in one place. Other modules read `settings`, not os.getenv.

Client-side credentials (QAUTO_EMAIL / QAUTO_PASSWORD) normally come from HTTP headers;
the values here are only the server-side fallback.
"""

import os
from dataclasses import dataclass
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
Transport = Literal["streamable-http", "stdio"]


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in ("0", "false", "no", "off", "")


def _env_choice[T: str](name: str, default: T, choices: tuple[T, ...]) -> T:
    value = os.getenv(name, default).strip()
    if name.endswith("LOG_LEVEL"):
        value = value.upper()
    if value not in choices:
        raise ValueError(f"{name} must be one of {', '.join(choices)}, got {value!r}")
    return value  # type: ignore[return-value]


LOG_LEVELS: tuple[LogLevel, ...] = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


@dataclass(frozen=True)
class Settings:
    # QAuto API
    base_url: str
    email: str | None
    password: str | None
    timeout: float
    # MCP transport
    mcp_transport: Transport
    mcp_host: str
    mcp_port: int
    mcp_http_path: str
    mcp_log_level: LogLevel
    # Application logging
    log_level: LogLevel
    log_http_bodies: bool
    log_body_max_chars: int


def load_settings() -> Settings:
    return Settings(
        base_url=os.getenv("QAUTO_BASE_URL", "https://qauto.forstudy.space/api"),
        email=os.getenv("QAUTO_EMAIL") or None,
        password=os.getenv("QAUTO_PASSWORD") or None,
        timeout=float(os.getenv("QAUTO_TIMEOUT", "30")),
        mcp_transport=_env_choice("MCP_TRANSPORT", "streamable-http", ("streamable-http", "stdio")),
        mcp_host=os.getenv("MCP_HOST", "127.0.0.1"),
        mcp_port=int(os.getenv("MCP_PORT", "8000")),
        mcp_http_path=os.getenv("MCP_HTTP_PATH", "/mcp"),
        mcp_log_level=_env_choice("MCP_LOG_LEVEL", "INFO", LOG_LEVELS),
        log_level=_env_choice("LOG_LEVEL", "INFO", LOG_LEVELS),
        log_http_bodies=_env_bool("LOG_HTTP_BODIES", True),
        log_body_max_chars=int(os.getenv("LOG_BODY_MAX_CHARS", "2000")),
    )


settings = load_settings()
