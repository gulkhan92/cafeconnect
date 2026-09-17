import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class TableSlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    date: datetime.date
    start_time: datetime.time
    end_time: datetime.time


class TableAvailabilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    table_number: str
    capacity: int
    location_tag: str | None
    available_slots: list[TableSlotOut] = Field(default_factory=list)
