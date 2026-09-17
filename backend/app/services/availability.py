import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.table import Table, TableSlot


async def get_available_tables(
    db: AsyncSession, date: datetime.date, party_size: int
) -> list[Table]:
    """Tables with capacity for party_size, each carrying only its open slots on `date`."""
    result = await db.execute(
        select(Table)
        .where(Table.capacity >= party_size)
        .options(
            selectinload(Table.slots.and_(TableSlot.date == date, TableSlot.is_booked.is_(False)))
        )
        .order_by(Table.table_number)
    )
    return list(result.scalars().unique().all())
