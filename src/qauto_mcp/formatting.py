"""One error format for all tools, so the model always gets the same text shape."""

from typing import Any

from mcp.server.mcpserver.exceptions import ToolError
from pydantic import ValidationError


def format_validation_error(exc: ValidationError) -> str:
    return "; ".join(f"{'.'.join(map(str, e['loc'])) or 'input'}: {e['msg']}" for e in exc.errors())


def invalid_input(exc: ValidationError) -> ToolError:
    return ToolError(f"Invalid input: {format_validation_error(exc)}")


def api_error(status_code: int, body: Any) -> ToolError:
    return ToolError(f"qauto API error {status_code}: {body}")
