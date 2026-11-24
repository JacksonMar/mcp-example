"""Resources: qauto://cars/catalog, qauto://cars/brands/{brand_id}."""

import json

from mcp.server.mcpserver import MCPServer

from qauto_mcp.services import catalog


def register_car_resources(mcp: MCPServer) -> None:
    @mcp.resource(
        "qauto://cars/catalog",
        name="car_catalog",
        title="Car catalog",
        description=(
            "Довідник усіх брендів і моделей qauto: carBrandId, carModelId і назви. "
            "Потрібен, щоб правильно викликати add_car. Це не список авто користувача."
        ),
        mime_type="application/json",
    )
    async def get_car_catalog() -> str:
        return json.dumps(await catalog.load_catalog(), ensure_ascii=False, indent=2)

    @mcp.resource(
        "qauto://cars/brands/{brand_id}",
        name="car_brand",
        title="Car brand models",
        description=(
            "Моделі одного бренду за carBrandId у URI, наприклад qauto://cars/brands/1 (Audi). "
            "Потрібен перед add_car. Це не список авто користувача."
        ),
        mime_type="application/json",
    )
    async def get_car_brand(brand_id: str) -> str:
        if not brand_id.isdigit():
            raise ValueError(f"brand_id must be a positive integer, got {brand_id!r}")
        brand = await catalog.find_brand(int(brand_id))
        if brand is None:
            raise ValueError(f"Brand {brand_id} not found. Read qauto://cars/catalog for valid ids.")
        return json.dumps(brand, ensure_ascii=False, indent=2)
