import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.enums import BookingSource
from app.models.table import Table, TableSlot


class BookingError(Exception):
    """Base class for booking-creation failures the caller must translate into a response."""


class SlotNotFoundError(BookingError):
    pass


class SlotAlreadyBookedError(BookingError):
    pass


class CapacityExceededError(BookingError):
    pass


async def create_booking(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    slot_id: uuid.UUID,
    party_size: int,
    created_via: BookingSource,
) -> Booking:
    """Atomically create a booking for a slot.

    Uses SELECT ... FOR UPDATE to lock the slot row so two concurrent requests
    for the same slot cannot both succeed: the loser blocks on the lock, then
    sees is_booked=True once the winner commits.

    populate_existing() is required here: a caller may have already loaded
    this same TableSlot via a plain (non-locking) query earlier in the same
    session (e.g. the chatbot checking availability first). Without it,
    SQLAlchemy's identity map would hand back that stale cached object
    instead of refreshing it from the row this query just locked, silently
    defeating the concurrency guarantee.
    """
    slot = (
        await db.execute(
            select(TableSlot)
            .where(TableSlot.id == slot_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()

    if slot is None:
        raise SlotNotFoundError()

    if slot.is_booked:
        raise SlotAlreadyBookedError()

    table = await db.get(Table, slot.table_id)
    if table is None or party_size > table.capacity:
        raise CapacityExceededError()

    booking = Booking(
        user_id=user_id,
        table_id=slot.table_id,
        slot_id=slot.id,
        party_size=party_size,
        created_via=created_via,
    )
    db.add(booking)
    await db.flush()

    slot.is_booked = True
    slot.booking_id = booking.id

    await db.commit()
    await db.refresh(booking)
    return booking
