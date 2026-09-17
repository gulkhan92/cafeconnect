import asyncio
import datetime
import os
import sys
from pathlib import Path

if sys.platform == "win32":
    # asyncpg's connection I/O breaks under Windows' default ProactorEventLoop
    # once a loop is torn down and recreated between fixtures/tests.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://cafeconnect:cafeconnect@localhost:5540/cafeconnect_test"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6390/1")
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-production")

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.redis import redis_client
from app.core.security import hash_password
from app.database import AsyncSessionLocal, engine
from app.main import app
from app.models.enums import UserRole
from app.models.menu import MenuCategory, MenuItem
from app.models.table import Table, TableSlot
from app.models.user import User

BACKEND_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(cfg, "head")
    yield
    command.downgrade(cfg, "base")


@pytest_asyncio.fixture(autouse=True)
async def clean_state():
    yield
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE TABLE users, menu_categories, menu_items, tables, "
                "table_slots, bookings, orders, order_items, chat_sessions, "
                "chat_messages RESTART IDENTITY CASCADE"
            )
        )
    await redis_client.flushdb()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def staff_user():
    password = "StaffPass123!"
    async with AsyncSessionLocal() as session:
        user = User(
            name="Staff Member",
            email="staff@example.com",
            hashed_password=hash_password(password),
            role=UserRole.staff_admin,
        )
        session.add(user)
        await session.commit()
    return {"email": "staff@example.com", "password": password}


@pytest_asyncio.fixture
async def customer_user():
    password = "CustomerPass123!"
    async with AsyncSessionLocal() as session:
        user = User(
            name="Regular Customer",
            email="customer@example.com",
            hashed_password=hash_password(password),
            role=UserRole.customer,
        )
        session.add(user)
        await session.commit()
    return {"email": "customer@example.com", "password": password}


async def get_access_token(client: AsyncClient, credentials: dict) -> str:
    response = await client.post("/auth/login", json=credentials)
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def sample_category():
    async with AsyncSessionLocal() as session:
        category = MenuCategory(name="Beverages", display_order=1)
        session.add(category)
        await session.commit()
        await session.refresh(category)
    return category


@pytest_asyncio.fixture
async def sample_table():
    async with AsyncSessionLocal() as session:
        table = Table(table_number="T1", capacity=4, location_tag="indoor")
        session.add(table)
        await session.commit()
        await session.refresh(table)
    return table


@pytest_asyncio.fixture
async def sample_slot(sample_table):
    async with AsyncSessionLocal() as session:
        slot = TableSlot(
            table_id=sample_table.id,
            date=datetime.date.today() + datetime.timedelta(days=1),
            start_time=datetime.time(18, 0),
            end_time=datetime.time(18, 30),
            is_booked=False,
        )
        session.add(slot)
        await session.commit()
        await session.refresh(slot)
    return slot


@pytest_asyncio.fixture
async def sample_menu_item(sample_category):
    async with AsyncSessionLocal() as session:
        item = MenuItem(
            category_id=sample_category.id,
            name="Cappuccino",
            description="Espresso with steamed milk foam",
            price=4.50,
            is_available=True,
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
    return item


@pytest_asyncio.fixture
async def unavailable_menu_item(sample_category):
    async with AsyncSessionLocal() as session:
        item = MenuItem(
            category_id=sample_category.id,
            name="Seasonal Pumpkin Spice Latte",
            description="Currently out of season",
            price=5.00,
            is_available=False,
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
    return item
