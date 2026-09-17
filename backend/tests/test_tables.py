import datetime

import pytest

from app.database import AsyncSessionLocal
from app.models.table import Table, TableSlot

pytestmark = pytest.mark.asyncio


async def test_availability_filters_by_capacity_and_booked_state(client, sample_table, sample_slot):
    async with AsyncSessionLocal() as session:
        small_table = Table(table_number="T2", capacity=2, location_tag="window")
        session.add(small_table)
        await session.commit()
        await session.refresh(small_table)

        booked_slot = TableSlot(
            table_id=sample_table.id,
            date=sample_slot.date,
            start_time=datetime.time(19, 0),
            end_time=datetime.time(19, 30),
            is_booked=True,
        )
        session.add(booked_slot)
        await session.commit()

    response = await client.get(
        "/tables/availability",
        params={"date": sample_slot.date.isoformat(), "party_size": 3},
    )
    assert response.status_code == 200
    body = response.json()

    table_numbers = {table["table_number"] for table in body}
    assert "T2" not in table_numbers

    sample_table_entry = next(t for t in body if t["id"] == str(sample_table.id))
    slot_start_times = {slot["start_time"] for slot in sample_table_entry["available_slots"]}
    assert "18:00:00" in slot_start_times
    assert "19:00:00" not in slot_start_times


async def test_availability_empty_for_unknown_date(client, sample_table, sample_slot):
    far_future = (sample_slot.date + datetime.timedelta(days=365)).isoformat()
    response = await client.get(
        "/tables/availability", params={"date": far_future, "party_size": 2}
    )
    assert response.status_code == 200
    body = response.json()
    assert all(table["available_slots"] == [] for table in body)
