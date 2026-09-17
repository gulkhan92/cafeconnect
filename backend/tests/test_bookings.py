import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.conftest import get_access_token

pytestmark = pytest.mark.asyncio


async def test_create_booking_succeeds_and_marks_slot_booked(client, customer_user, sample_slot):
    headers = {"Authorization": f"Bearer {await get_access_token(client, customer_user)}"}

    response = await client.post(
        "/bookings", json={"slot_id": str(sample_slot.id), "party_size": 2}, headers=headers
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["slot_id"] == str(sample_slot.id)

    availability = await client.get(
        "/tables/availability",
        params={"date": sample_slot.date.isoformat(), "party_size": 1},
    )
    slots = availability.json()[0]["available_slots"]
    assert slots == []


async def test_create_booking_rejects_party_size_over_capacity(client, customer_user, sample_slot):
    headers = {"Authorization": f"Bearer {await get_access_token(client, customer_user)}"}
    response = await client.post(
        "/bookings", json={"slot_id": str(sample_slot.id), "party_size": 99}, headers=headers
    )
    assert response.status_code == 400


async def test_create_booking_requires_auth(client, sample_slot):
    response = await client.post("/bookings", json={"slot_id": str(sample_slot.id), "party_size": 2})
    assert response.status_code == 401


async def test_double_booking_same_slot_is_rejected(client, customer_user, sample_slot):
    headers = {"Authorization": f"Bearer {await get_access_token(client, customer_user)}"}
    first = await client.post(
        "/bookings", json={"slot_id": str(sample_slot.id), "party_size": 2}, headers=headers
    )
    assert first.status_code == 201

    second = await client.post(
        "/bookings", json={"slot_id": str(sample_slot.id), "party_size": 2}, headers=headers
    )
    assert second.status_code == 409


async def test_concurrent_bookings_for_same_slot_exactly_one_succeeds(customer_user, sample_slot):
    """The core race-condition guarantee from the plan: two simultaneous booking
    requests for the same slot must not both succeed."""

    async def attempt_booking() -> int:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            token = await get_access_token(ac, customer_user)
            response = await ac.post(
                "/bookings",
                json={"slot_id": str(sample_slot.id), "party_size": 2},
                headers={"Authorization": f"Bearer {token}"},
            )
            return response.status_code

    results = await asyncio.gather(attempt_booking(), attempt_booking())

    assert sorted(results) == [201, 409]


async def test_staff_can_list_and_cancel_booking(client, staff_user, customer_user, sample_slot):
    customer_headers = {
        "Authorization": f"Bearer {await get_access_token(client, customer_user)}"
    }
    created = await client.post(
        "/bookings",
        json={"slot_id": str(sample_slot.id), "party_size": 2},
        headers=customer_headers,
    )
    booking_id = created.json()["id"]

    staff_headers = {"Authorization": f"Bearer {await get_access_token(client, staff_user)}"}

    listing = await client.get(
        "/bookings", params={"date": sample_slot.date.isoformat()}, headers=staff_headers
    )
    assert listing.status_code == 200
    assert any(b["id"] == booking_id for b in listing.json())

    forbidden = await client.get("/bookings", headers=customer_headers)
    assert forbidden.status_code == 403

    cancel = await client.patch(
        f"/bookings/{booking_id}", json={"status": "cancelled"}, headers=staff_headers
    )
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"

    availability = await client.get(
        "/tables/availability",
        params={"date": sample_slot.date.isoformat(), "party_size": 1},
    )
    slots = availability.json()[0]["available_slots"]
    assert len(slots) == 1


async def test_list_my_bookings_only_returns_own(client, customer_user, staff_user, sample_slot):
    customer_headers = {
        "Authorization": f"Bearer {await get_access_token(client, customer_user)}"
    }
    await client.post(
        "/bookings", json={"slot_id": str(sample_slot.id), "party_size": 2}, headers=customer_headers
    )

    staff_headers = {"Authorization": f"Bearer {await get_access_token(client, staff_user)}"}
    response = await client.get("/bookings/me", headers=staff_headers)
    assert response.status_code == 200
    assert response.json() == []

    own = await client.get("/bookings/me", headers=customer_headers)
    assert len(own.json()) == 1
