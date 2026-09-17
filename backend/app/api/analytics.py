import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.daterange import InvalidRangeError, resolve_range
from app.core.deps import require_role
from app.database import get_db
from app.models.enums import UserRole
from app.schemas.analytics import (
    ConversionResponse,
    DashboardSummary,
    RevenueSummary,
    TableUtilizationResponse,
    TopItemsResponse,
)
from app.services import analytics as analytics_service

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(require_role(UserRole.staff_admin))],
)


def _resolve_or_400(range_: str, start: datetime.date | None, end: datetime.date | None):
    try:
        return resolve_range(range_, start, end)
    except InvalidRangeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(db: AsyncSession = Depends(get_db)) -> DashboardSummary:
    return await analytics_service.get_dashboard_summary(db)


@router.get("/revenue", response_model=RevenueSummary)
async def revenue(
    range: str = Query(default="today"),
    start: datetime.date | None = Query(default=None),
    end: datetime.date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> RevenueSummary:
    start_dt, end_dt, start_date, end_date = _resolve_or_400(range, start, end)
    return await analytics_service.get_revenue_summary(db, start_dt, end_dt, start_date, end_date)


@router.get("/top-items", response_model=TopItemsResponse)
async def top_items(
    range: str = Query(default="today"),
    start: datetime.date | None = Query(default=None),
    end: datetime.date | None = Query(default=None),
    limit: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> TopItemsResponse:
    start_dt, end_dt, start_date, end_date = _resolve_or_400(range, start, end)
    return await analytics_service.get_top_items(db, start_dt, end_dt, start_date, end_date, limit)


@router.get("/table-utilization", response_model=TableUtilizationResponse)
async def table_utilization(
    range: str = Query(default="today"),
    start: datetime.date | None = Query(default=None),
    end: datetime.date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> TableUtilizationResponse:
    _, _, start_date, end_date = _resolve_or_400(range, start, end)
    return await analytics_service.get_table_utilization(db, start_date, end_date)


@router.get("/conversion", response_model=ConversionResponse)
async def conversion(
    range: str = Query(default="today"),
    start: datetime.date | None = Query(default=None),
    end: datetime.date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> ConversionResponse:
    start_dt, end_dt, start_date, end_date = _resolve_or_400(range, start, end)
    return await analytics_service.get_conversion(db, start_dt, end_dt, start_date, end_date)
