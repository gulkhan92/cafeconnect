import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.enums import BookingSource, BookingStatus, OrderDataSource, OrderStatus
from app.models.menu import MenuItem
from app.models.order import Order, OrderItem
from app.models.table import Table, TableSlot
from app.schemas.analytics import (
    ConversionResponse,
    DashboardSummary,
    HourlyBookingCount,
    RevenuePoint,
    RevenueSummary,
    TableUtilization,
    TableUtilizationResponse,
    TopItem,
    TopItemsResponse,
)

# Live-only: seed/demo data (Order.source == "seed_demo") is always excluded so
# the dashboard reflects genuine business activity from day one, per the plan.
_LIVE_ORDER_FILTER = (Order.source == OrderDataSource.live, Order.status != OrderStatus.cancelled)


async def get_revenue_summary(
    db: AsyncSession,
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    start_date: datetime.date,
    end_date: datetime.date,
) -> RevenueSummary:
    filters = (*_LIVE_ORDER_FILTER, Order.created_at >= start_dt, Order.created_at < end_dt)

    total_revenue, order_count = (
        await db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0), func.count(Order.id)).where(*filters)
        )
    ).one()

    day = func.date(Order.created_at)
    series_rows = (
        await db.execute(
            select(day.label("day"), func.coalesce(func.sum(Order.total_amount), 0), func.count(Order.id))
            .where(*filters)
            .group_by(day)
            .order_by(day)
        )
    ).all()

    average_order_value = (total_revenue / order_count) if order_count else Decimal("0")

    return RevenueSummary(
        range_start=start_date,
        range_end=end_date,
        total_revenue=total_revenue,
        order_count=order_count,
        average_order_value=average_order_value,
        series=[RevenuePoint(date=row[0], revenue=row[1], order_count=row[2]) for row in series_rows],
    )


async def get_top_items(
    db: AsyncSession,
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    start_date: datetime.date,
    end_date: datetime.date,
    limit: int = 5,
) -> TopItemsResponse:
    quantity_sold = func.coalesce(func.sum(OrderItem.quantity), 0)
    revenue = func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price_at_order_time), 0)

    base_query = (
        select(MenuItem.id, MenuItem.name, quantity_sold, revenue)
        .select_from(OrderItem)
        .join(Order, OrderItem.order_id == Order.id)
        .join(MenuItem, OrderItem.menu_item_id == MenuItem.id)
        .where(*_LIVE_ORDER_FILTER, Order.created_at >= start_dt, Order.created_at < end_dt)
        .group_by(MenuItem.id, MenuItem.name)
    )

    by_quantity_rows = (await db.execute(base_query.order_by(quantity_sold.desc()).limit(limit))).all()
    by_revenue_rows = (await db.execute(base_query.order_by(revenue.desc()).limit(limit))).all()

    def to_items(rows) -> list[TopItem]:
        return [TopItem(menu_item_id=r[0], name=r[1], quantity_sold=r[2], revenue=r[3]) for r in rows]

    return TopItemsResponse(
        range_start=start_date,
        range_end=end_date,
        by_quantity=to_items(by_quantity_rows),
        by_revenue=to_items(by_revenue_rows),
    )


async def get_table_utilization(
    db: AsyncSession, start_date: datetime.date, end_date: datetime.date
) -> TableUtilizationResponse:
    slots_subq = (
        select(TableSlot.table_id, func.count(TableSlot.id).label("total_slots"))
        .where(TableSlot.date >= start_date, TableSlot.date <= end_date)
        .group_by(TableSlot.table_id)
        .subquery()
    )

    booked_subq = (
        select(TableSlot.table_id, func.count(Booking.id).label("booked_slots"))
        .select_from(Booking)
        .join(TableSlot, Booking.slot_id == TableSlot.id)
        .where(
            TableSlot.date >= start_date,
            TableSlot.date <= end_date,
            Booking.status != BookingStatus.cancelled,
        )
        .group_by(TableSlot.table_id)
        .subquery()
    )

    rows = (
        await db.execute(
            select(
                Table.id,
                Table.table_number,
                func.coalesce(slots_subq.c.total_slots, 0),
                func.coalesce(booked_subq.c.booked_slots, 0),
            )
            .select_from(Table)
            .outerjoin(slots_subq, slots_subq.c.table_id == Table.id)
            .outerjoin(booked_subq, booked_subq.c.table_id == Table.id)
            .order_by(Table.table_number)
        )
    ).all()

    tables = [
        TableUtilization(
            table_id=row[0],
            table_number=row[1],
            total_slots=row[2],
            booked_slots=row[3],
            occupancy_rate=(row[3] / row[2]) if row[2] else 0.0,
        )
        for row in rows
    ]

    hour = func.extract("hour", TableSlot.start_time)
    peak_rows = (
        await db.execute(
            select(hour.label("hour"), func.count(Booking.id))
            .select_from(Booking)
            .join(TableSlot, Booking.slot_id == TableSlot.id)
            .where(
                TableSlot.date >= start_date,
                TableSlot.date <= end_date,
                Booking.status != BookingStatus.cancelled,
            )
            .group_by(hour)
            .order_by(hour)
        )
    ).all()

    return TableUtilizationResponse(
        range_start=start_date,
        range_end=end_date,
        tables=tables,
        peak_hours=[HourlyBookingCount(hour=int(row[0]), booking_count=row[1]) for row in peak_rows],
    )


async def get_conversion(
    db: AsyncSession,
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    start_date: datetime.date,
    end_date: datetime.date,
) -> ConversionResponse:
    date_filter = (Booking.created_at >= start_dt, Booking.created_at < end_dt)

    total_bookings = (await db.execute(select(func.count(Booking.id)).where(*date_filter))).scalar_one()

    bookings_with_order = (
        await db.execute(
            select(func.count(func.distinct(Booking.id)))
            .select_from(Booking)
            .join(Order, Order.booking_id == Booking.id)
            .where(*date_filter)
        )
    ).scalar_one()

    source_rows = (
        await db.execute(
            select(Booking.created_via, func.count(Booking.id))
            .where(*date_filter)
            .group_by(Booking.created_via)
        )
    ).all()
    counts_by_source = dict(source_rows)

    return ConversionResponse(
        range_start=start_date,
        range_end=end_date,
        total_bookings=total_bookings,
        bookings_with_order=bookings_with_order,
        conversion_rate=(bookings_with_order / total_bookings) if total_bookings else 0.0,
        chatbot_bookings=counts_by_source.get(BookingSource.chatbot, 0),
        manual_bookings=counts_by_source.get(BookingSource.manual, 0),
    )


async def get_dashboard_summary(db: AsyncSession) -> DashboardSummary:
    today = datetime.date.today()
    start_dt = datetime.datetime.combine(today, datetime.time.min)
    end_dt = start_dt + datetime.timedelta(days=1)

    today_revenue = (
        await db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                *_LIVE_ORDER_FILTER, Order.created_at >= start_dt, Order.created_at < end_dt
            )
        )
    ).scalar_one()

    today_bookings = (
        await db.execute(
            select(func.count(Booking.id)).where(
                Booking.created_at >= start_dt, Booking.created_at < end_dt
            )
        )
    ).scalar_one()

    active_orders = (
        await db.execute(
            select(func.count(Order.id)).where(
                Order.source == OrderDataSource.live,
                Order.status.in_([OrderStatus.placed, OrderStatus.preparing, OrderStatus.ready]),
            )
        )
    ).scalar_one()

    return DashboardSummary(
        today_revenue=today_revenue, today_bookings=today_bookings, active_orders=active_orders
    )
