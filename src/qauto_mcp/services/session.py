"""Session logic: which credentials to use, and when to sign in again.

Credential priority:
  1. tool arguments (explicit signin / signup);
  2. HTTP headers of the current MCP request (QAUTO_EMAIL / QAUTO_PASSWORD,
     or X-QAuto-Email / X-QAuto-Password);
  3. server env (QAUTO_EMAIL / QAUTO_PASSWORD in .env) as fallback.

The process has one shared cookie jar, so it holds one `sid` at a time.
An explicit signin/signup keeps its session. An automatic session is
renewed when the configured email changes (for example, other headers).
"""

from collections.abc import Mapping
from typing import Any

from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import ValidationError

from qauto_mcp.config import settings
from qauto_mcp.formatting import invalid_input
from qauto_mcp.logging_setup import get_logger
from qauto_mcp.models.auth import SignInInput
from qauto_mcp.services.http_client import call_api

logger = get_logger(__name__)

EMAIL_HEADERS = ("qauto_email", "x-qauto-email")
PASSWORD_HEADERS = ("qauto_password", "x-qauto-password")

_session_email: str | None = None
_session_is_explicit: bool = False


def _first_header(headers: Mapping[str, str], names: tuple[str, ...]) -> str | None:
    for name in names:
        value = (headers.get(name) or "").strip()
        if value:
            return value
    return None


def header_credentials(ctx: Context | None) -> tuple[str | None, str | None]:
    """Read credentials from the HTTP headers of the current request. stdio has no headers."""
    if ctx is None:
        return None, None
    try:
        raw = ctx.headers
    except ValueError:  # Context outside of a request
        return None, None
    if not raw:
        return None, None
    headers = {k.lower(): v for k, v in raw.items()}
    return _first_header(headers, EMAIL_HEADERS), _first_header(headers, PASSWORD_HEADERS)


def resolve_credentials(
    email: str | None = None, password: str | None = None, ctx: Context | None = None
) -> tuple[str, str]:
    if email and password:
        return email, password
    header_email, header_password = header_credentials(ctx)
    if header_email and header_password:
        return header_email, header_password
    if settings.email and settings.password:
        return settings.email, settings.password
    raise ToolError(
        "QAUTO_EMAIL and QAUTO_PASSWORD must be set in MCP client headers "
        "(mcp.json → headers) or in server env as fallback."
    )


def mark_signed_in(email: str, *, is_explicit: bool) -> None:
    global _session_email, _session_is_explicit
    _session_email = email
    _session_is_explicit = is_explicit


async def signin_as(data: SignInInput, *, is_explicit: bool) -> Any:
    body = await call_api("POST", "/auth/signin", data.to_payload())
    mark_signed_in(data.email, is_explicit=is_explicit)
    return body


async def ensure_signed_in(ctx: Context | None) -> None:
    """Sign in automatically before a tool that needs a session."""
    if _session_email and _session_is_explicit:
        return
    email, password = resolve_credentials(ctx=ctx)
    if _session_email == email:
        return
    logger.info("auto signin (session email changed: %s → %s)", _session_email or "none", email)
    try:
        data = SignInInput(email=email, password=password)
    except ValidationError as exc:
        raise invalid_input(exc) from exc
    await signin_as(data, is_explicit=False)
