import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.intent import classify_intent
from app.core.llm.router import AllProvidersUnavailableError, LLMRouter
from app.core.logging_config import log_event
from app.models.chat import ChatMessage, ChatSession
from app.models.enums import BookingSource, ChatRole
from app.models.table import Table, TableSlot
from app.models.user import User
from app.schemas.chat import ChatMessageResponse
from app.services.availability import get_available_tables
from app.services.bookings import (
    CapacityExceededError,
    SlotAlreadyBookedError,
    SlotNotFoundError,
    create_booking,
)
from app.services.menu import search_menu_items

MAX_MENU_RESULTS = 3

UNAVAILABLE_PROVIDERS_REPLY = (
    "I'm having trouble understanding booking requests right now since both of our "
    "assistants are temporarily unavailable. Please call the cafe directly, or use "
    "the availability page to book manually."
)

UNKNOWN_INTENT_REPLY = (
    "Sorry, I'm not sure I understood that. I can help you check table availability, "
    "book a table, or answer questions about our menu."
)

ORDER_ITEM_REPLY = (
    "Online ordering isn't available quite yet, but you're welcome to browse our menu "
    "in the meantime."
)


async def _get_or_create_session(
    db: AsyncSession, session_id: uuid.UUID | None, user: User | None
) -> ChatSession:
    if session_id is not None:
        existing = await db.get(ChatSession, session_id)
        if existing is not None:
            return existing

    session = ChatSession(user_id=user.id if user else None)
    db.add(session)
    await db.flush()
    return session


async def _append_message(db: AsyncSession, session: ChatSession, role: ChatRole, content: str) -> None:
    db.add(ChatMessage(session_id=session.id, role=role, content=content))


def _handle_small_talk(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ("thank", "thanks")):
        return "You're very welcome! Anything else I can help with?"
    if any(word in lowered for word in ("bye", "goodbye", "see you")):
        return "Goodbye! We hope to see you at the cafe soon."
    return "Hi there! I can help you check availability, book a table, or answer menu questions."


async def _handle_menu_question(db: AsyncSession, text: str, ordering_context: bool = False) -> str:
    matches = await search_menu_items(db, text, limit=MAX_MENU_RESULTS)
    if not matches:
        return "I couldn't find any menu items matching that — could you rephrase?"

    listing = "; ".join(f"{item.name} (${item.price})" for item, _score in matches)
    prefix = f"{ORDER_ITEM_REPLY} Here's what I found: " if ordering_context else "Here's what I found: "
    return f"{prefix}{listing}."


def _find_candidate_slot(
    tables: list[Table], requested_time: datetime.time | None
) -> tuple[Table, TableSlot] | None:
    for table in tables:
        for slot in sorted(table.slots, key=lambda s: s.start_time):
            if requested_time is None or slot.start_time == requested_time:
                return table, slot
    return None


def _list_alternatives(tables: list[Table], limit: int = 3) -> list[str]:
    alternatives = []
    for table in tables:
        for slot in sorted(table.slots, key=lambda s: s.start_time):
            alternatives.append(f"{table.table_number} at {slot.start_time.strftime('%H:%M')}")
            if len(alternatives) >= limit:
                return alternatives
    return alternatives


async def _handle_booking_intent(
    db: AsyncSession, llm_router: LLMRouter, user: User | None, text: str, intent: str
) -> tuple[str, dict | None, str | None]:
    today = datetime.date.today().isoformat()

    try:
        extraction, provider_used = await llm_router.extract_booking_fields(text, today)
    except AllProvidersUnavailableError:
        return UNAVAILABLE_PROVIDERS_REPLY, None, None

    missing = [field for field in ("date", "party_size") if getattr(extraction, field) is None]
    if missing:
        return (
            f"I'd love to help with that! Could you tell me the {' and '.join(missing)}?",
            {"extracted": extraction.model_dump()},
            provider_used,
        )

    try:
        booking_date = datetime.date.fromisoformat(extraction.date)
    except ValueError:
        return (
            "Sorry, I couldn't understand that date — could you try a format like 2026-09-20?",
            None,
            provider_used,
        )

    tables = await get_available_tables(db, booking_date, extraction.party_size)
    if extraction.table_preference:
        preferred = [t for t in tables if t.location_tag == extraction.table_preference]
        if preferred:
            tables = preferred

    requested_time: datetime.time | None = None
    if extraction.time:
        try:
            requested_time = datetime.time.fromisoformat(extraction.time)
        except ValueError:
            requested_time = None

    candidate = _find_candidate_slot(tables, requested_time)

    if candidate is None:
        alternatives = _list_alternatives(tables)
        if alternatives:
            return (
                f"I couldn't find a table exactly matching that time on {extraction.date}. "
                f"Open options: {'; '.join(alternatives)}. Would any of those work?",
                {"alternatives": alternatives},
                provider_used,
            )
        return (
            f"Sorry, we don't have any tables available on {extraction.date} for a party of "
            f"{extraction.party_size}.",
            None,
            provider_used,
        )

    table, slot = candidate

    if intent == "check_availability":
        return (
            f"Yes! Table {table.table_number} is available on {extraction.date} at "
            f"{slot.start_time.strftime('%H:%M')} (seats up to {table.capacity}). "
            "Would you like me to book it for you?",
            {"table_number": table.table_number, "slot_id": str(slot.id)},
            provider_used,
        )

    if user is None:
        return (
            "Please log in so I can complete the booking for you, or use the availability "
            "page to book manually.",
            {"table_number": table.table_number, "slot_id": str(slot.id)},
            provider_used,
        )

    try:
        booking = await create_booking(
            db,
            user_id=user.id,
            slot_id=slot.id,
            party_size=extraction.party_size,
            created_via=BookingSource.chatbot,
        )
    except SlotAlreadyBookedError:
        return (
            "Sorry, that table was just booked by someone else — could you try a different time?",
            None,
            provider_used,
        )
    except CapacityExceededError:
        return (
            "That table doesn't fit your party size — could you adjust the number of guests?",
            None,
            provider_used,
        )
    except SlotNotFoundError:
        return ("Sorry, I couldn't find that slot anymore — please try again.", None, provider_used)

    return (
        f"You're booked! Table {table.table_number} on {extraction.date} at "
        f"{slot.start_time.strftime('%H:%M')} for {extraction.party_size} guests. See you then!",
        {"booking_id": str(booking.id), "status": booking.status.value},
        provider_used,
    )


async def handle_chat_message(
    db: AsyncSession,
    llm_router: LLMRouter,
    session_id: uuid.UUID | None,
    text: str,
    user: User | None,
) -> ChatMessageResponse:
    session = await _get_or_create_session(db, session_id, user)
    await _append_message(db, session, ChatRole.user, text)

    intent, _confidence, method = await classify_intent(text)
    provider_used: str | None = None
    data: dict | None = None

    if method == "unknown":
        try:
            intent, provider_used = await llm_router.classify_intent(
                text, ["book_table", "check_availability", "menu_question", "order_item", "small_talk"]
            )
        except AllProvidersUnavailableError:
            intent = "unknown"

    if intent == "menu_question":
        reply = await _handle_menu_question(db, text)
    elif intent in ("book_table", "check_availability"):
        reply, data, booking_provider = await _handle_booking_intent(db, llm_router, user, text, intent)
        provider_used = provider_used or booking_provider
    elif intent == "order_item":
        reply = await _handle_menu_question(db, text, ordering_context=True)
    elif intent == "small_talk":
        reply = _handle_small_talk(text)
    else:
        reply = UNKNOWN_INTENT_REPLY

    session.last_intent = intent
    await _append_message(db, session, ChatRole.assistant, reply)
    await db.commit()

    log_event(
        "chat_turn_completed",
        session_id=str(session.id),
        user_id=str(user.id) if user else None,
        intent=intent,
        classification_method=method,
        provider_used=provider_used,
    )

    return ChatMessageResponse(
        session_id=session.id, intent=intent, reply=reply, provider_used=provider_used, data=data
    )
