"""Server assembly: MCPServer + lifespan + registration + logging. No HTTP logic and no models here."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter
from typing import Any

from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from starlette.requests import Request
from starlette.responses import JSONResponse

from qauto_mcp import logging_setup
from qauto_mcp.config import settings
from qauto_mcp.logging_setup import get_logger, redact_mapping
from qauto_mcp.prompts import register_prompts
from qauto_mcp.resources import register_resources
from qauto_mcp.services.http_client import close_client, open_client
from qauto_mcp.tools import register_tools

logger = get_logger(__name__)

INSTRUCTIONS = (
    "MCP server for the QAuto garage API. "
    "Auth: add_car and get_cars sign in automatically with QAUTO_EMAIL / QAUTO_PASSWORD "
    "from the client headers (fallback: server env); signup or signin set the session cookie sid explicitly. "
    "Before add_car, read resource qauto://cars/catalog (or call get_brands / get_models) for valid ids. "
    "For a garage overview use prompt analyze_cars."
)


class LoggingMCPServer(MCPServer):
    """Logs every incoming tool call in one place: name, masked arguments, result, time."""

    async def call_tool(self, name: str, arguments: dict[str, Any], context: Context | None = None) -> Any:
        started = perf_counter()
        logger.info("tool → %s %s", name, redact_mapping(arguments))
        try:
            result = await super().call_tool(name, arguments, context)
        except ToolError as exc:
            logger.warning("tool ✗ %s (%.0f ms): %s", name, _ms(started), exc)
            raise
        except Exception:
            logger.exception("tool ✗ %s (%.0f ms)", name, _ms(started))
            raise
        logger.info("tool ← %s ok (%.0f ms)", name, _ms(started))
        return result


def _ms(started: float) -> float:
    return (perf_counter() - started) * 1000


@asynccontextmanager
async def app_lifespan(_server: MCPServer) -> AsyncIterator[None]:
    open_client()
    try:
        yield
    finally:
        await close_client()


mcp = LoggingMCPServer(
    name="qauto-mcp",
    instructions=INSTRUCTIONS,
    lifespan=app_lifespan,
    log_level=settings.mcp_log_level,
)
logging_setup.configure()  # after the constructor: MCPServer.__init__ calls logging.basicConfig


@mcp.custom_route("/health", methods=["GET"])
async def health(_request: Request) -> JSONResponse:
    """Liveness check for Docker / Compose. Not an MCP endpoint, works only with streamable-http."""
    return JSONResponse({"status": "ok", "mcp": settings.mcp_http_path})


register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)
