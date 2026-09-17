import datetime
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.booking import Booking
from app.models.enums import BookingSource, BookingStatus, OrderDataSource, OrderStatus
from app.models.menu import MenuItem
from app.models.order import Order, OrderItem
from app.models.table import TableSlot
from app.models.user import User
from tests.conftest import get_access_token

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def analytics_scenario(sample_category, sample_table, sample_menu_item, customer_user):
    """Builds a controlled set of today's data with a known, hand-computed
    expected result, so every analytics assertion below is checking real
    arithmetic rather than "some number came back".
    """
    today = datetime.date.today()
    now = datetime.datetime.combine(today, datetime.time(12, 0))

    async with AsyncSessionLocal() as session:
        customer = (
            await session.execute(select(User).where(User.email == "customer@example.com"))
        ).scalar_one()

        item_b = MenuItem(
            category_id=sample_category.id, name="Item B", price=Decimal("6.00"), is_available=True
        )
        session.add(item_b)
        await session.flush()

        # Live orders that should be counted.
        order1 = Order(
            user_id=customer.id, status=OrderStatus.completed, source=OrderDataSource.live,
            total_amount=Decimal("15.00"), created_at=now,
        )
        order1.items = [
            OrderItem(menu_item_id=sample_menu_item.id, quantity=2, unit_price_at_order_time=Decimal("4.50")),
            OrderItem(menu_item_id=item_b.id, quantity=1, unit_price_at_order_time=Decimal("6.00")),
        ]
        order2 = Order(
            user_id=customer.id, status=OrderStatus.placed, source=OrderDataSource.live,
            total_amount=Decimal("4.50"), created_at=now,
        )
        order2.items = [
            OrderItem(menu_item_id=sample_menu_item.id, quantity=1, unit_price_at_order_time=Decimal("4.50")),
        ]

        # Must be excluded: cancelled, and seed_demo source.
        order3 = Order(
            user_id=customer.id, status=OrderStatus.cancelled, source=OrderDataSource.live,
            total_amount=Decimal("22.50"), created_at=now,
        )
        order3.items = [
            OrderItem(menu_item_id=sample_menu_item.id, quantity=5, unit_price_at_order_time=Decimal("4.50")),
        ]
        order4 = Order(
            user_id=customer.id, status=OrderStatus.completed, source=OrderDataSource.seed_demo,
            total_amount=Decimal("450.00"), created_at=now,
        )
        order4.items = [
            OrderItem(
                menu_item_id=sample_menu_item.id, quantity=100, unit_price_at_order_time=Decimal("4.50")
            ),
        ]

        session.add_all([order1, order2, order3, order4])

        slot_a = TableSlot(
            table_id=sample_table.id,
            date=today,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(9, 30),
        )
        slot_b = TableSlot(
            table_id=sample_table.id,
            date=today,
            start_time=datetime.time(10, 0),
            end_time=datetime.time(10, 30),
        )
        slot_c = TableSlot(
            table_id=sample_table.id,
            date=today,
            start_time=datetime.time(11, 0),
            end_time=datetime.time(11, 30),
        )
        session.add_all([slot_a, slot_b, slot_c])
        await session.flush()

        booking_confirmed = Booking(
            user_id=customer.id, table_id=sample_table.id, slot_id=slot_a.id, party_size=2,
            status=BookingStatus.confirmed, created_via=BookingSource.manual, created_at=now,
        )
        booking_cancelled = Booking(
            user_id=customer.id, table_id=sample_table.id, slot_id=slot_b.id, party_size=2,
            status=BookingStatus.cancelled, created_via=BookingSource.chatbot, created_at=now,
        )
        session.add_all([booking_confirmed, booking_cancelled])
        await session.flush()

        # Link order1 to the confirmed booking for conversion tracking.
        order1.booking_id = booking_confirmed.id

        await session.commit()

    return {
        "today": today,
        "table_id": str(sample_table.id),
        "item_a_id": str(sample_menu_item.id),
        "item_b_id": str(item_b.id),
    }


async def _staff_headers(client, staff_user):
    return {"Authorization": f"Bearer {await get_access_token(client, staff_user)}"}


async def test_analytics_requires_staff_role(client, customer_user):
    headers = {"Authorization": f"Bearer {await get_access_token(client, customer_user)}"}
    paths = (
        "/analytics/summary",
        "/analytics/revenue",
        "/analytics/top-items",
        "/analytics/table-utilization",
        "/analytics/conversion",
    )
    for path in paths:
        response = await client.get(path, headers=headers)
        assert response.status_code == 403, path


async def test_revenue_excludes_cancelled_and_seed_demo(client, staff_user, analytics_scenario):
    headers = await _staff_headers(client, staff_user)
    response = await client.get("/analytics/revenue", params={"range": "today"}, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_revenue"] == "19.50"
    assert body["order_count"] == 2
    assert body["average_order_value"] == "9.75"
    assert len(body["series"]) == 1
    assert body["series"][0]["revenue"] == "19.50"


async def test_top_items_ranks_by_quantity_and_revenue(client, staff_user, analytics_scenario):
    headers = await _staff_headers(client, staff_user)
    response = await client.get("/analytics/top-items", params={"range": "today"}, headers=headers)
    assert response.status_code == 200
    body = response.json()

    by_quantity = {row["name"]: row["quantity_sold"] for row in body["by_quantity"]}
    assert by_quantity["Cappuccino"] == 3  # 2 (order1) + 1 (order2); cancelled/demo excluded
    assert by_quantity["Item B"] == 1

    by_revenue = {row["name"]: row["revenue"] for row in body["by_revenue"]}
    assert by_revenue["Cappuccino"] == "13.50"
    assert by_revenue["Item B"] == "6.00"
    assert body["by_revenue"][0]["name"] == "Cappuccino"  # highest revenue first


async def test_table_utilization_computes_occupancy_and_peak_hours(client, staff_user, analytics_scenario):
    headers = await _staff_headers(client, staff_user)
    response = await client.get("/analytics/table-utilization", params={"range": "today"}, headers=headers)
    assert response.status_code == 200
    body = response.json()

    table = next(t for t in body["tables"] if t["table_id"] == analytics_scenario["table_id"])
    assert table["total_slots"] == 3
    assert table["booked_slots"] == 1  # only the confirmed booking counts, not the cancelled one
    assert table["occupancy_rate"] == pytest.approx(1 / 3)

    peak_hours = {row["hour"]: row["booking_count"] for row in body["peak_hours"]}
    assert peak_hours == {9: 1}  # only the confirmed booking's slot hour


async def test_conversion_rate_and_booking_source_counts(client, staff_user, analytics_scenario):
    headers = await _staff_headers(client, staff_user)
    response = await client.get("/analytics/conversion", params={"range": "today"}, headers=headers)
    assert response.status_code == 200
    body = response.json()

    assert body["total_bookings"] == 2
    assert body["bookings_with_order"] == 1
    assert body["conversion_rate"] == pytest.approx(0.5)
    assert body["manual_bookings"] == 1
    assert body["chatbot_bookings"] == 1


async def test_dashboard_summary_reflects_todays_activity(client, staff_user, analytics_scenario):
    headers = await _staff_headers(client, staff_user)
    response = await client.get("/analytics/summary", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["today_revenue"] == "19.50"
    assert body["today_bookings"] == 2
    assert body["active_orders"] == 1  # order2 is "placed"; order1 "completed" doesn't count


async def test_custom_range_requires_start_and_end(client, staff_user):
    headers = await _staff_headers(client, staff_user)
    response = await client.get("/analytics/revenue", params={"range": "custom"}, headers=headers)
    assert response.status_code == 400


async def test_invalid_range_name_is_rejected(client, staff_user):
    headers = await _staff_headers(client, staff_user)
    response = await client.get("/analytics/revenue", params={"range": "decade"}, headers=headers)
    assert response.status_code == 400


async def test_custom_range_with_explicit_dates(client, staff_user, analytics_scenario):
    headers = await _staff_headers(client, staff_user)
    today = analytics_scenario["today"].isoformat()
    response = await client.get(
        "/analytics/revenue", params={"range": "custom", "start": today, "end": today}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["total_revenue"] == "19.50"
