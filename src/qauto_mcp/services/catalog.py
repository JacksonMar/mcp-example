"""Brand/model reference data from the QAuto API, for resources and catalog tools."""

from typing import Any

from qauto_mcp.services.http_client import call_api


async def get_brands() -> Any:
    return await call_api("GET", "/cars/brands")


async def get_models(car_brand_id: int | None = None) -> Any:
    body = await call_api("GET", "/cars/models")
    if car_brand_id is not None:
        body["data"] = [m for m in body["data"] if m["carBrandId"] == car_brand_id]
    return body


async def load_catalog() -> list[dict[str, Any]]:
    """Read brands and models from the API and group the models by brand."""
    brands = (await get_brands())["data"]
    models = (await get_models())["data"]
    return [
        {
            "carBrandId": b["id"],
            "brand": b["title"],
            "models": [
                {"carModelId": m["id"], "model": m["title"]}
                for m in models
                if m["carBrandId"] == b["id"]
            ],
        }
        for b in brands
    ]


async def find_brand(brand_id: int) -> dict[str, Any] | None:
    for brand in await load_catalog():
        if brand["carBrandId"] == brand_id:
            return brand
    return None
