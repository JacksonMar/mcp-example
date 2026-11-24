"""Input model for add_car. No network, no MCP."""

from pydantic import BaseModel, Field


class AddCarInput(BaseModel):
    carBrandId: int = Field(gt=0)
    carModelId: int = Field(gt=0)
    mileage: int = Field(ge=0, le=999999)

    def to_payload(self) -> dict[str, int]:
        return self.model_dump()
