import asyncio
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
        await conn.execute(text("TRUNCATE TABLE users CASCADE"))
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
