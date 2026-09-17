import json

from google import genai
from google.genai import types

from app.core.llm.base import (
    BOOKING_EXTRACTION_SYSTEM_PROMPT,
    INTENT_CLASSIFY_SYSTEM_PROMPT,
    BookingExtraction,
    ProviderError,
)

_EXTRACTION_FIELDS = ("date", "time", "party_size", "table_preference")


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self._client = genai.Client(api_key=api_key) if api_key else None
        self._model = model

    def _client_or_raise(self) -> genai.Client:
        if self._client is None:
            raise ProviderError("Gemini API key is not configured")
        return self._client

    async def extract_booking_fields(self, text: str, today: str) -> BookingExtraction:
        client = self._client_or_raise()
        prompt = f"{BOOKING_EXTRACTION_SYSTEM_PROMPT}\nToday's date is {today}. Message: {text}"
        try:
            response = await client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=100,
                    temperature=0,
                    response_mime_type="application/json",
                ),
            )
            content = response.text
        except Exception as exc:
            raise ProviderError(str(exc)) from exc

        try:
            data = json.loads(content)
        except (json.JSONDecodeError, TypeError) as exc:
            raise ProviderError(f"Invalid JSON from provider: {content!r}") from exc

        return BookingExtraction(**{field: data.get(field) for field in _EXTRACTION_FIELDS})

    async def classify_intent(self, text: str, labels: list[str]) -> str:
        client = self._client_or_raise()
        prompt = f"{INTENT_CLASSIFY_SYSTEM_PROMPT}\nLabels: {', '.join(labels)}\nMessage: {text}"
        try:
            response = await client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(max_output_tokens=10, temperature=0),
            )
            label = (response.text or "").strip().lower()
        except Exception as exc:
            raise ProviderError(str(exc)) from exc

        return label if label in labels else "unknown"
