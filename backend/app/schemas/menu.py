import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class MenuItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_id: uuid.UUID
    name: str
    description: str | None
    price: Decimal
    image_url: str | None
    is_available: bool


class MenuCategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    display_order: int
    items: list[MenuItemOut] = Field(default_factory=list)


class MenuSearchResult(BaseModel):
    item: MenuItemOut
    score: float = Field(description="Cosine similarity to the query, 1.0 = identical")


class MenuItemCreate(BaseModel):
    category_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(gt=0, decimal_places=2)
    image_url: str | None = Field(default=None, max_length=500)
    is_available: bool = True


class MenuItemUpdate(BaseModel):
    category_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    image_url: str | None = Field(default=None, max_length=500)
    is_available: bool | None = None
