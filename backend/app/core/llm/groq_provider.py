import json

from groq import AsyncGroq

from app.core.llm.base import (
    BOOKING_EXTRACTION_SYSTEM_PROMPT,
    INTENT_CLASSIFY_SYSTEM_PROMPT,
    BookingExtraction,
    ProviderError,
)

_EXTRACTION_FIELDS = ("date", "time", "party_size", "table_preference")


class GroqProvider:
    name = "groq"

    def __init__(self, api_key: str, model: str = "openai/gpt-oss-20b"):
        self._client = AsyncGroq(api_key=api_key) if api_key else None
        self._model = model

    def _client_or_raise(self) -> AsyncGroq:
        if self._client is None:
            raise ProviderError("Groq API key is not configured")
        return self._client

    async def extract_booking_fields(self, text: str, today: str) -> BookingExtraction:
        client = self._client_or_raise()
        try:
            response = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": BOOKING_EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Today's date is {today}. Message: {text}"},
                ],
                max_tokens=100,
                temperature=0,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
        except Exception as exc:
            raise ProviderError(str(exc)) from exc

        try:
            data = json.loads(content)
        except (json.JSONDecodeError, TypeError) as exc:
            raise ProviderError(f"Invalid JSON from provider: {content!r}") from exc

        return BookingExtraction(**{field: data.get(field) for field in _EXTRACTION_FIELDS})

    async def classify_intent(self, text: str, labels: list[str]) -> str:
        client = self._client_or_raise()
        try:
            response = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": INTENT_CLASSIFY_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Labels: {', '.join(labels)}\nMessage: {text}"},
                ],
                max_tokens=10,
                temperature=0,
            )
            label = (response.choices[0].message.content or "").strip().lower()
        except Exception as exc:
            raise ProviderError(str(exc)) from exc

        return label if label in labels else "unknown"
