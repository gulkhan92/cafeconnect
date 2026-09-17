from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.admin import router as admin_router
from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.bookings import router as bookings_router
from app.api.chat import router as chat_router
from app.api.menu import router as menu_router
from app.api.orders import router as orders_router
from app.api.tables import router as tables_router
from app.api.users import router as users_router
from app.core.config import assert_production_secrets_are_safe, settings
from app.core.limiter import limiter
from app.core.logging_config import RequestLoggingMiddleware, configure_logging


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    assert_production_secrets_are_safe()
    yield


app = FastAPI(title="CafeConnect API", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(menu_router)
app.include_router(tables_router)
app.include_router(bookings_router)
app.include_router(chat_router)
app.include_router(orders_router)
app.include_router(analytics_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
