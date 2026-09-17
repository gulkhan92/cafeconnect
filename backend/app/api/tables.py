import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.table import Table
from app.schemas.table import TableAvailabilityOut
from app.services.availability import get_available_tables

router = APIRouter(prefix="/tables", tags=["tables"])


@router.get("/availability", response_model=list[TableAvailabilityOut])
async def get_availability(
    date: datetime.date = Query(...),
    party_size: int = Query(gt=0),
    db: AsyncSession = Depends(get_db),
) -> list[Table]:
    tables = await get_available_tables(db, date, party_size)

    return [
        TableAvailabilityOut(
            id=table.id,
            table_number=table.table_number,
            capacity=table.capacity,
            location_tag=table.location_tag,
            available_slots=sorted(table.slots, key=lambda slot: slot.start_time),
        )
        for table in tables
    ]
