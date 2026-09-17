import pytest

from app.database import AsyncSessionLocal
from app.models.menu import MenuItem
from tests.conftest import get_access_token

pytestmark = pytest.mark.asyncio


async def test_create_order_computes_total_from_server_side_price(
    client, customer_user, sample_menu_item
):
    headers = {"Authorization": f"Bearer {await get_access_token(client, customer_user)}"}

    response = await client.post(
        "/orders",
        json={"items": [{"menu_item_id": str(sample_menu_item.id), "quantity": 3}]},
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "placed"
    assert body["total_amount"] == "13.50"
    assert len(body["items"]) == 1
    assert body["items"][0]["unit_price_at_order_time"] == "4.50"


async def test_create_order_ignores_client_submitted_price(client, customer_user, sample_menu_item):
    """The schema has no price field for the client to submit at all — this
    proves the server never even looks at extra client-supplied pricing data."""
    headers = {"Authorization": f"Bearer {await get_access_token(client, customer_user)}"}

    response = await client.post(
        "/orders",
        json={
            "items": [
                {"menu_item_id": str(sample_menu_item.id), "quantity": 1, "unit_price_at_order_time": "0.01"}
            ]
        },
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["items"][0]["unit_price_at_order_time"] == "4.50"


async def test_create_order_rejects_unavailable_item(client, customer_user, unavailable_menu_item):
    headers = {"Authorization": f"Bearer {await get_access_token(client, customer_user)}"}
    response = await client.post(
        "/orders",
        json={"items": [{"menu_item_id": str(unavailable_menu_item.id), "quantity": 1}]},
        headers=headers,
    )
    assert response.status_code == 400


async def test_create_order_rejects_unknown_menu_item(client, customer_user):
    headers = {"Authorization": f"Bearer {await get_access_token(client, customer_user)}"}
    response = await client.post(
        "/orders",
        json={"items": [{"menu_item_id": "00000000-0000-0000-0000-000000000000", "quantity": 1}]},
        headers=headers,
    )
    assert response.status_code == 404


async def test_create_order_requires_auth(client, sample_menu_item):
    response = await client.post(
        "/orders", json={"items": [{"menu_item_id": str(sample_menu_item.id), "quantity": 1}]}
    )
    assert response.status_code == 401


async def test_order_can_link_to_own_booking(client, customer_user, sample_menu_item, sample_slot):
    headers = {"Authorization": f"Bearer {await get_access_token(client, customer_user)}"}
    booking = await client.post(
        "/bookings", json={"slot_id": str(sample_slot.id), "party_size": 2}, headers=headers
    )
    booking_id = booking.json()["id"]

    response = await client.post(
        "/orders",
        json={
            "items": [{"menu_item_id": str(sample_menu_item.id), "quantity": 1}],
            "booking_id": booking_id,
        },
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["booking_id"] == booking_id


async def test_order_rejects_someone_elses_booking(
    client, customer_user, staff_user, sample_menu_item, sample_slot
):
    staff_headers = {"Authorization": f"Bearer {await get_access_token(client, staff_user)}"}
    other_booking = await client.post(
        "/bookings", json={"slot_id": str(sample_slot.id), "party_size": 2}, headers=staff_headers
    )
    other_booking_id = other_booking.json()["id"]

    customer_headers = {"Authorization": f"Bearer {await get_access_token(client, customer_user)}"}
    response = await client.post(
        "/orders",
        json={
            "items": [{"menu_item_id": str(sample_menu_item.id), "quantity": 1}],
            "booking_id": other_booking_id,
        },
        headers=customer_headers,
    )
    assert response.status_code == 403


async def test_list_my_orders_only_returns_own(client, customer_user, staff_user, sample_menu_item):
    customer_headers = {"Authorization": f"Bearer {await get_access_token(client, customer_user)}"}
    await client.post(
        "/orders",
        json={"items": [{"menu_item_id": str(sample_menu_item.id), "quantity": 1}]},
        headers=customer_headers,
    )

    staff_headers = {"Authorization": f"Bearer {await get_access_token(client, staff_user)}"}
    staff_own_orders = await client.get("/orders/me", headers=staff_headers)
    assert staff_own_orders.json() == []

    own = await client.get("/orders/me", headers=customer_headers)
    assert len(own.json()) == 1


async def test_customer_cannot_list_all_orders(client, customer_user):
    headers = {"Authorization": f"Bearer {await get_access_token(client, customer_user)}"}
    response = await client.get("/orders", headers=headers)
    assert response.status_code == 403


async def test_staff_can_filter_orders_by_status(client, customer_user, staff_user, sample_menu_item):
    customer_headers = {"Authorization": f"Bearer {await get_access_token(client, customer_user)}"}
    created = await client.post(
        "/orders",
        json={"items": [{"menu_item_id": str(sample_menu_item.id), "quantity": 2}]},
        headers=customer_headers,
    )
    order_id = created.json()["id"]

    staff_headers = {"Authorization": f"Bearer {await get_access_token(client, staff_user)}"}

    placed = await client.get("/orders", params={"status": "placed"}, headers=staff_headers)
    assert any(o["id"] == order_id for o in placed.json())

    ready = await client.get("/orders", params={"status": "ready"}, headers=staff_headers)
    assert all(o["id"] != order_id for o in ready.json())


async def test_staff_progresses_order_through_valid_statuses(
    client, customer_user, staff_user, sample_menu_item
):
    customer_headers = {"Authorization": f"Bearer {await get_access_token(client, customer_user)}"}
    created = await client.post(
        "/orders",
        json={"items": [{"menu_item_id": str(sample_menu_item.id), "quantity": 1}]},
        headers=customer_headers,
    )
    order_id = created.json()["id"]

    staff_headers = {"Authorization": f"Bearer {await get_access_token(client, staff_user)}"}

    for next_status in ("preparing", "ready", "completed"):
        response = await client.patch(
            f"/orders/{order_id}", json={"status": next_status}, headers=staff_headers
        )
        assert response.status_code == 200, response.text
        assert response.json()["status"] == next_status


async def test_staff_cannot_skip_statuses_or_move_backwards(
    client, customer_user, staff_user, sample_menu_item
):
    customer_headers = {"Authorization": f"Bearer {await get_access_token(client, customer_user)}"}
    created = await client.post(
        "/orders",
        json={"items": [{"menu_item_id": str(sample_menu_item.id), "quantity": 1}]},
        headers=customer_headers,
    )
    order_id = created.json()["id"]

    staff_headers = {"Authorization": f"Bearer {await get_access_token(client, staff_user)}"}

    skip_ahead = await client.patch(
        f"/orders/{order_id}", json={"status": "completed"}, headers=staff_headers
    )
    assert skip_ahead.status_code == 400

    await client.patch(f"/orders/{order_id}", json={"status": "preparing"}, headers=staff_headers)
    move_backwards = await client.patch(
        f"/orders/{order_id}", json={"status": "placed"}, headers=staff_headers
    )
    assert move_backwards.status_code == 400


async def test_customer_cannot_update_order_status(client, customer_user, sample_menu_item):
    headers = {"Authorization": f"Bearer {await get_access_token(client, customer_user)}"}
    created = await client.post(
        "/orders",
        json={"items": [{"menu_item_id": str(sample_menu_item.id), "quantity": 1}]},
        headers=headers,
    )
    order_id = created.json()["id"]

    response = await client.patch(f"/orders/{order_id}", json={"status": "preparing"}, headers=headers)
    assert response.status_code == 403


async def test_menu_item_deletion_still_restricted_once_ordered(
    client, staff_user, customer_user, sample_menu_item
):
    """Confirms the Phase 1 ON DELETE RESTRICT FK is still honored once an
    order actually references the item (Phase 3's delete endpoint already
    handles the IntegrityError; this exercises it end-to-end)."""
    customer_headers = {"Authorization": f"Bearer {await get_access_token(client, customer_user)}"}
    await client.post(
        "/orders",
        json={"items": [{"menu_item_id": str(sample_menu_item.id), "quantity": 1}]},
        headers=customer_headers,
    )

    staff_headers = {"Authorization": f"Bearer {await get_access_token(client, staff_user)}"}
    response = await client.delete(f"/menu/items/{sample_menu_item.id}", headers=staff_headers)
    assert response.status_code == 409

    async with AsyncSessionLocal() as session:
        assert await session.get(MenuItem, sample_menu_item.id) is not None
