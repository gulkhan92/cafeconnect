import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import BookingSource, BookingStatus


class BookingCreate(BaseModel):
    slot_id: uuid.UUID
    party_size: int = Field(gt=0)
    created_via: BookingSource = BookingSource.manual


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    table_id: uuid.UUID
    slot_id: uuid.UUID
    party_size: int
    status: BookingStatus
    created_via: BookingSource
    created_at: datetime.datetime


class BookingStatusUpdate(BaseModel):
    status: BookingStatus
