import datetime
import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import OrderDataSource, OrderStatus


class OrderItemCreate(BaseModel):
    menu_item_id: uuid.UUID
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)
    booking_id: uuid.UUID | None = None


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    menu_item_id: uuid.UUID
    quantity: int
    unit_price_at_order_time: Decimal


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    booking_id: uuid.UUID | None
    status: OrderStatus
    total_amount: Decimal
    source: OrderDataSource
    created_at: datetime.datetime
    items: list[OrderItemOut] = Field(default_factory=list)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
