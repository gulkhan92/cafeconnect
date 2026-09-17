from typing import Protocol

from pydantic import BaseModel

# Kept short and static so it benefits from provider-side prompt caching, and
# because the model never needs to see the previous turns of the conversation.
BOOKING_EXTRACTION_SYSTEM_PROMPT = (
    "You extract table booking details from a customer's message and output JSON only, "
    "no prose, no markdown fences. Keys: "
    'date (string "YYYY-MM-DD" or null), '
    'time (string 24-hour "HH:MM" or null), '
    "party_size (integer or null), "
    'table_preference (one of "window", "patio", "indoor", or null). '
    "If a field is not mentioned or unclear, use null for it."
)

INTENT_CLASSIFY_SYSTEM_PROMPT = (
    "Classify the customer's message into exactly one label from the given list. "
    "Reply with only the label text and nothing else."
)


class BookingExtraction(BaseModel):
    date: str | None = None
    time: str | None = None
    party_size: int | None = None
    table_preference: str | None = None


class ProviderError(Exception):
    """A provider call failed: missing key, network error, rate limit, or bad response."""


class LLMProvider(Protocol):
    name: str

    async def extract_booking_fields(self, text: str, today: str) -> BookingExtraction: ...

    async def classify_intent(self, text: str, labels: list[str]) -> str: ...
