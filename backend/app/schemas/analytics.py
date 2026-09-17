import datetime
import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class RevenuePoint(BaseModel):
    date: datetime.date
    revenue: Decimal
    order_count: int


class RevenueSummary(BaseModel):
    range_start: datetime.date
    range_end: datetime.date
    total_revenue: Decimal
    order_count: int
    average_order_value: Decimal
    series: list[RevenuePoint] = Field(default_factory=list)


class TopItem(BaseModel):
    menu_item_id: uuid.UUID
    name: str
    quantity_sold: int
    revenue: Decimal


class TopItemsResponse(BaseModel):
    range_start: datetime.date
    range_end: datetime.date
    by_quantity: list[TopItem] = Field(default_factory=list)
    by_revenue: list[TopItem] = Field(default_factory=list)


class TableUtilization(BaseModel):
    table_id: uuid.UUID
    table_number: str
    total_slots: int
    booked_slots: int
    occupancy_rate: float


class HourlyBookingCount(BaseModel):
    hour: int
    booking_count: int


class TableUtilizationResponse(BaseModel):
    range_start: datetime.date
    range_end: datetime.date
    tables: list[TableUtilization] = Field(default_factory=list)
    peak_hours: list[HourlyBookingCount] = Field(default_factory=list)


class ConversionResponse(BaseModel):
    range_start: datetime.date
    range_end: datetime.date
    total_bookings: int
    bookings_with_order: int
    conversion_rate: float
    chatbot_bookings: int
    manual_bookings: int


class DashboardSummary(BaseModel):
    today_revenue: Decimal
    today_bookings: int
    active_orders: int
