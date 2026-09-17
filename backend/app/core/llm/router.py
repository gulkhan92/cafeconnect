from app.core.llm.base import BookingExtraction, LLMProvider, ProviderError
from app.core.llm.quota import is_quota_exceeded, record_call
from app.core.logging_config import log_event


class AllProvidersUnavailableError(Exception):
    """Raised when every configured provider is over quota, unconfigured, or erroring."""


class LLMRouter:
    """Tries providers in priority order, skipping any already at its per-minute
    quota and failing over to the next one on a provider error (e.g. a 429).
    """

    def __init__(self, providers: list[tuple[LLMProvider, int]]):
        self._providers = providers

    async def _run(self, method_name: str, *args) -> tuple[object, str]:
        last_error: Exception | None = None

        for provider, requests_per_minute in self._providers:
            if await is_quota_exceeded(provider.name, requests_per_minute):
                log_event("llm_provider_skipped_quota", provider=provider.name, method=method_name)
                continue
            try:
                await record_call(provider.name)
                result = await getattr(provider, method_name)(*args)
                log_event("llm_provider_served_request", provider=provider.name, method=method_name)
                return result, provider.name
            except ProviderError as exc:
                last_error = exc
                log_event(
                    "llm_provider_failed_over", provider=provider.name, method=method_name, error=str(exc)
                )
                continue

        last_error_str = str(last_error) if last_error else None
        log_event("llm_all_providers_unavailable", method=method_name, error=last_error_str)
        raise AllProvidersUnavailableError(last_error_str or "no LLM providers available")

    async def extract_booking_fields(self, text: str, today: str) -> tuple[BookingExtraction, str]:
        return await self._run("extract_booking_fields", text, today)

    async def classify_intent(self, text: str, labels: list[str]) -> tuple[str, str]:
        return await self._run("classify_intent", text, labels)


_router_singleton: LLMRouter | None = None


def get_llm_router() -> LLMRouter:
    global _router_singleton
    if _router_singleton is None:
        from app.core.config import settings
        from app.core.llm.gemini_provider import GeminiProvider
        from app.core.llm.groq_provider import GroqProvider

        _router_singleton = LLMRouter(
            [
                (GroqProvider(settings.groq_api_key, settings.groq_model), settings.groq_requests_per_minute),
                (
                    GeminiProvider(settings.gemini_api_key, settings.gemini_model),
                    settings.gemini_requests_per_minute,
                ),
            ]
        )
    return _router_singleton
