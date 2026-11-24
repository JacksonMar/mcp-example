"""Tools: add_car, get_cars, get_brands, get_models."""

from typing import Any

from mcp.server.mcpserver import Context, MCPServer
from mcp_types import ToolAnnotations
from pydantic import ValidationError

from qauto_mcp.formatting import invalid_input
from qauto_mcp.models.cars import AddCarInput
from qauto_mcp.services import catalog
from qauto_mcp.services.http_client import call_api
from qauto_mcp.services.session import ensure_signed_in

READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True)


def register_car_tools(mcp: MCPServer) -> None:
    @mcp.tool(
        name="add_car",
        title="Add car to garage",
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=True),
    )
    async def add_car(ctx: Context, carBrandId: int, carModelId: int, mileage: int) -> dict[str, Any]:
        """Add a car to the garage of the current user (POST /cars).

        Needs a session. If there is none, the tool signs in automatically
        with credentials from the MCP client headers or the server env.
        """
        try:
            data = AddCarInput(carBrandId=carBrandId, carModelId=carModelId, mileage=mileage)
        except ValidationError as exc:
            raise invalid_input(exc) from exc

        await ensure_signed_in(ctx)
        return await call_api("POST", "/cars", data.to_payload())

    @mcp.tool(name="get_cars", title="List user cars", annotations=READ_ONLY)
    async def get_cars(ctx: Context) -> dict[str, Any]:
        """Return all cars of the current user (GET /cars).

        Needs a session. If there is none, the tool signs in automatically
        with credentials from the MCP client headers or the server env.
        """
        await ensure_signed_in(ctx)
        return await call_api("GET", "/cars")

    @mcp.tool(name="get_brands", title="List car brands", annotations=READ_ONLY)
    async def get_brands() -> dict[str, Any]:
        """Return all car brands (GET /cars/brands).

        Use the brand `id` as carBrandId in add_car. No session is needed.
        """
        return await catalog.get_brands()

    @mcp.tool(name="get_models", title="List car models", annotations=READ_ONLY)
    async def get_models(carBrandId: int | None = None) -> dict[str, Any]:
        """Return car models (GET /cars/models).

        If carBrandId is given, the tool returns only the models of that brand.
        Use the model `id` as carModelId in add_car. No session is needed.
        """
        return await catalog.get_models(carBrandId)
