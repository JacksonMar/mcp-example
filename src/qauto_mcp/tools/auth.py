"""Tools: signup, signin."""

from typing import Any

from mcp.server.mcpserver import Context, MCPServer
from mcp_types import ToolAnnotations
from pydantic import ValidationError

from qauto_mcp.formatting import invalid_input
from qauto_mcp.models.auth import SignInInput, SignUpInput
from qauto_mcp.services.http_client import call_api
from qauto_mcp.services.session import mark_signed_in, resolve_credentials, signin_as


def register_auth_tools(mcp: MCPServer) -> None:
    @mcp.tool(
        name="signup",
        title="Sign up to QAuto",
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=True),
    )
    async def signup(name: str, lastName: str, email: str, password: str, repeatPassword: str) -> dict[str, Any]:
        """Register a new qauto user (POST /auth/signup).

        Rules: name and lastName 2-20 chars; password 8-15 chars with an uppercase
        letter, a lowercase letter and a digit; repeatPassword equal to password.
        After success the session cookie `sid` stays in the server's HTTP client.
        """
        try:
            data = SignUpInput(
                name=name,
                lastName=lastName,
                email=email,
                password=password,
                repeatPassword=repeatPassword,
            )
        except ValidationError as exc:
            raise invalid_input(exc) from exc

        body = await call_api("POST", "/auth/signup", data.to_payload())
        mark_signed_in(data.email, is_explicit=True)
        return body

    @mcp.tool(
        name="signin",
        title="Sign in to QAuto",
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=True),
    )
    async def signin(ctx: Context, email: str | None = None, password: str | None = None) -> dict[str, Any]:
        """Sign in to an existing qauto account (POST /auth/signin).

        If email or password is not given, the tool uses QAUTO_EMAIL and
        QAUTO_PASSWORD from the MCP client headers, then from the server env.
        After success the session cookie `sid` stays in the shared HTTP client
        for add_car and get_cars.
        """
        is_explicit = bool(email and password)
        email, password = resolve_credentials(email, password, ctx)
        try:
            data = SignInInput(email=email, password=password)
        except ValidationError as exc:
            raise invalid_input(exc) from exc

        return await signin_as(data, is_explicit=is_explicit)
