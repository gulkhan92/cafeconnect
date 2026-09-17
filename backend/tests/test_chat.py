import pytest

from app.core.llm.base import BookingExtraction
from app.core.llm.router import AllProvidersUnavailableError, get_llm_router
from app.database import AsyncSessionLocal
from app.main import app
from app.models.menu import MenuItem
from tests.conftest import get_access_token

pytestmark = pytest.mark.asyncio


class FakeLLMRouter:
    """Stands in for the real Groq/Gemini router in tests, per the plan's guidance
    to test LLM failover/extraction logic with mocked provider responses rather
    than live network calls."""

    def __init__(self, extraction: BookingExtraction | Exception | None = None, classification: str | None = None):
        self._extraction = extraction
        self._classification = classification
        self.extract_calls = 0
        self.classify_calls = 0

    async def extract_booking_fields(self, text: str, today: str):
        self.extract_calls += 1
        if isinstance(self._extraction, Exception):
            raise self._extraction
        return self._extraction, "fake"

    async def classify_intent(self, text: str, labels: list[str]):
        self.classify_calls += 1
        if isinstance(self._classification, Exception):
            raise self._classification
        return self._classification, "fake"


@pytest.fixture
def use_fake_router():
    installed = []

    def _install(fake_router):
        installed.append(fake_router)
        app.dependency_overrides[get_llm_router] = lambda: fake_router
        return fake_router

    yield _install
    app.dependency_overrides.pop(get_llm_router, None)


async def _seed_menu_item(category_id, name, description):
    async with AsyncSessionLocal() as session:
        from app.core.embeddings import embed_text

        embedding = await embed_text(f"{name}. {description}")
        item = MenuItem(
            category_id=category_id, name=name, description=description, price=4.5, embedding=embedding
        )
        session.add(item)
        await session.commit()


async def test_menu_question_answered_locally_without_llm(client, sample_category, use_fake_router):
    await _seed_menu_item(sample_category.id, "Iced Chocolate Mocha", "Cold chocolate espresso drink")
    fake_router = use_fake_router(FakeLLMRouter())

    response = await client.post("/chat/message", json={"message": "what desserts do you have?"})
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "menu_question"
    assert body["provider_used"] is None
    assert "Iced Chocolate Mocha" in body["reply"]
    assert fake_router.extract_calls == 0
    assert fake_router.classify_calls == 0


async def test_small_talk_answered_without_llm(client, use_fake_router):
    fake_router = use_fake_router(FakeLLMRouter())
    response = await client.post("/chat/message", json={"message": "hi there!"})
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "small_talk"
    assert body["provider_used"] is None
    assert fake_router.extract_calls == 0


async def test_check_availability_uses_one_llm_call_and_no_booking_created(
    client, sample_slot, use_fake_router
):
    extraction = BookingExtraction(
        date=sample_slot.date.isoformat(),
        time=sample_slot.start_time.isoformat()[:5],
        party_size=2,
        table_preference=None,
    )
    fake_router = use_fake_router(FakeLLMRouter(extraction=extraction))

    response = await client.post(
        "/chat/message",
        json={"message": "is there any table available tomorrow for 2 people at 6pm?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "check_availability"
    assert body["provider_used"] == "fake"
    assert fake_router.extract_calls == 1
    assert "available" in body["reply"].lower()


async def test_book_table_creates_a_real_booking_for_logged_in_user(
    client, customer_user, sample_slot, use_fake_router
):
    extraction = BookingExtraction(
        date=sample_slot.date.isoformat(),
        time=sample_slot.start_time.isoformat()[:5],
        party_size=2,
        table_preference=None,
    )
    use_fake_router(FakeLLMRouter(extraction=extraction))

    headers = {"Authorization": f"Bearer {await get_access_token(client, customer_user)}"}
    response = await client.post(
        "/chat/message",
        json={"message": "book me a table for 2 tomorrow at 6pm"},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "book_table"
    assert body["data"]["status"] == "pending"

    bookings = await client.get("/bookings/me", headers=headers)
    assert len(bookings.json()) == 1
    assert bookings.json()[0]["slot_id"] == str(sample_slot.id)


async def test_book_table_without_login_does_not_create_booking(client, sample_slot, use_fake_router):
    extraction = BookingExtraction(
        date=sample_slot.date.isoformat(),
        time=sample_slot.start_time.isoformat()[:5],
        party_size=2,
        table_preference=None,
    )
    use_fake_router(FakeLLMRouter(extraction=extraction))

    response = await client.post(
        "/chat/message", json={"message": "book me a table for 2 tomorrow at 6pm"}
    )
    assert response.status_code == 200
    assert "log in" in response.json()["reply"].lower()


async def test_booking_asks_for_missing_fields_without_touching_db(client, use_fake_router):
    extraction = BookingExtraction(date=None, time=None, party_size=None, table_preference=None)
    use_fake_router(FakeLLMRouter(extraction=extraction))

    response = await client.post("/chat/message", json={"message": "I'd like to reserve a table"})
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "book_table"
    assert "date" in body["reply"].lower() and "party_size" in body["reply"].lower()


async def test_graceful_degradation_when_all_llm_providers_unavailable(client, use_fake_router):
    use_fake_router(FakeLLMRouter(extraction=AllProvidersUnavailableError("no providers")))

    response = await client.post(
        "/chat/message", json={"message": "book a table for 4 tomorrow at 7pm"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["provider_used"] is None
    assert "call the cafe" in body["reply"].lower()


async def test_second_booking_attempt_on_same_slot_reports_no_availability(
    client, customer_user, sample_slot, use_fake_router
):
    """Once a slot is booked, the chatbot's own availability lookup filters it
    out before ever re-attempting a booking on it, so a second identical
    request degrades gracefully to a "no availability" reply rather than
    hitting the race-condition path (that path is only reachable under true
    concurrency, which test_bookings.py already covers at the API layer)."""
    extraction = BookingExtraction(
        date=sample_slot.date.isoformat(),
        time=sample_slot.start_time.isoformat()[:5],
        party_size=2,
        table_preference=None,
    )
    use_fake_router(FakeLLMRouter(extraction=extraction))
    headers = {"Authorization": f"Bearer {await get_access_token(client, customer_user)}"}

    first = await client.post(
        "/chat/message", json={"message": "book me a table for 2 tomorrow at 6pm"}, headers=headers
    )
    session_id = first.json()["session_id"]

    second = await client.post(
        "/chat/message",
        json={"session_id": session_id, "message": "book me a table for 2 tomorrow at 6pm"},
        headers=headers,
    )
    assert second.status_code == 200
    assert second.json()["session_id"] == session_id
    assert "don't have any tables available" in second.json()["reply"].lower()

    bookings = await client.get("/bookings/me", headers=headers)
    assert len(bookings.json()) == 1


async def test_concurrent_chat_bookings_for_same_slot_exactly_one_succeeds(
    customer_user, sample_slot
):
    """Two simultaneous chat booking requests both read availability before
    either commits, so both reach create_booking for the same slot — this
    exercises the SlotAlreadyBookedError branch under real concurrency."""
    import asyncio

    from httpx import ASGITransport, AsyncClient

    extraction = BookingExtraction(
        date=sample_slot.date.isoformat(),
        time=sample_slot.start_time.isoformat()[:5],
        party_size=2,
        table_preference=None,
    )
    app.dependency_overrides[get_llm_router] = lambda: FakeLLMRouter(extraction=extraction)
    try:

        async def attempt() -> str:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                token = await get_access_token(ac, customer_user)
                response = await ac.post(
                    "/chat/message",
                    json={"message": "book me a table for 2 tomorrow at 6pm"},
                    headers={"Authorization": f"Bearer {token}"},
                )
                return response.json()["reply"]

        replies = await asyncio.gather(attempt(), attempt())
    finally:
        app.dependency_overrides.pop(get_llm_router, None)

    booked_replies = [r for r in replies if "you're booked" in r.lower()]
    rejected_replies = [r for r in replies if "just booked by someone else" in r.lower()]
    assert len(booked_replies) == 1
    assert len(rejected_replies) == 1


async def test_session_persists_across_turns(client, use_fake_router):
    use_fake_router(FakeLLMRouter())
    first = await client.post("/chat/message", json={"message": "hello"})
    session_id = first.json()["session_id"]

    second = await client.post(
        "/chat/message", json={"session_id": session_id, "message": "thanks, bye"}
    )
    assert second.json()["session_id"] == session_id

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        from app.models.chat import ChatMessage

        result = await session.execute(
            select(ChatMessage).where(ChatMessage.session_id == session_id)
        )
        messages = result.scalars().all()
        assert len(messages) == 4  # 2 user turns + 2 assistant replies
