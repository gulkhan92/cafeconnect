"""One-time seed script for Phase 1: default admin user, tables, and 30 days of slots.

Run with:
    python -m scripts.seed
"""
import asyncio
import datetime as dt
import os

from sqlalchemy import select

from app.core.security import hash_password
from app.database import AsyncSessionLocal
from app.models.enums import UserRole
from app.models.table import Table, TableSlot
from app.models.user import User

DEFAULT_ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@cafeconnect.io")
DEFAULT_ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "ChangeMe123!")

DEFAULT_TABLES = [
    {"table_number": "T1", "capacity": 2, "location_tag": "window"},
    {"table_number": "T2", "capacity": 2, "location_tag": "window"},
    {"table_number": "T3", "capacity": 4, "location_tag": "indoor"},
    {"table_number": "T4", "capacity": 4, "location_tag": "indoor"},
    {"table_number": "T5", "capacity": 6, "location_tag": "indoor"},
    {"table_number": "T6", "capacity": 2, "location_tag": "patio"},
    {"table_number": "T7", "capacity": 4, "location_tag": "patio"},
    {"table_number": "T8", "capacity": 8, "location_tag": "indoor"},
]

OPENING_TIME = dt.time(9, 0)
CLOSING_TIME = dt.time(22, 0)
SLOT_MINUTES = 30
SEED_DAYS_AHEAD = 30


async def seed_admin_user(session) -> None:
    existing = await session.scalar(select(User).where(User.email == DEFAULT_ADMIN_EMAIL))
    if existing:
        print(f"Admin user already exists: {DEFAULT_ADMIN_EMAIL}")
        return

    admin = User(
        name="Cafe Admin",
        email=DEFAULT_ADMIN_EMAIL,
        hashed_password=hash_password(DEFAULT_ADMIN_PASSWORD),
        role=UserRole.staff_admin,
    )
    session.add(admin)
    print(f"Created admin user: {DEFAULT_ADMIN_EMAIL} / {DEFAULT_ADMIN_PASSWORD}")


async def seed_tables(session) -> list[Table]:
    existing = (await session.scalars(select(Table))).all()
    if existing:
        print(f"Tables already seeded ({len(existing)} found).")
        return list(existing)

    tables = [Table(**data) for data in DEFAULT_TABLES]
    session.add_all(tables)
    await session.flush()
    print(f"Created {len(tables)} tables.")
    return tables


def _generate_daily_slots() -> list[tuple[dt.time, dt.time]]:
    slots = []
    current = dt.datetime.combine(dt.date.today(), OPENING_TIME)
    end_of_day = dt.datetime.combine(dt.date.today(), CLOSING_TIME)
    delta = dt.timedelta(minutes=SLOT_MINUTES)
    while current + delta <= end_of_day:
        slots.append((current.time(), (current + delta).time()))
        current += delta
    return slots


async def seed_slots(session, tables: list[Table]) -> None:
    existing_count = await session.scalar(select(TableSlot.id).limit(1))
    if existing_count:
        print("Table slots already seeded.")
        return

    daily_slots = _generate_daily_slots()
    today = dt.date.today()
    slot_rows = []
    for day_offset in range(SEED_DAYS_AHEAD):
        slot_date = today + dt.timedelta(days=day_offset)
        for table in tables:
            for start_time, end_time in daily_slots:
                slot_rows.append(
                    TableSlot(
                        table_id=table.id,
                        date=slot_date,
                        start_time=start_time,
                        end_time=end_time,
                        is_booked=False,
                    )
                )
    session.add_all(slot_rows)
    print(f"Created {len(slot_rows)} table slots across {SEED_DAYS_AHEAD} days.")


async def main() -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await seed_admin_user(session)
            tables = await seed_tables(session)
            await seed_slots(session, tables)
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
