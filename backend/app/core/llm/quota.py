from app.core.redis import redis_client

_WINDOW_SECONDS = 60


def _minute_key(provider_name: str) -> str:
    return f"llm_calls:{provider_name}:minute"


async def record_call(provider_name: str) -> int:
    key = _minute_key(provider_name)
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, _WINDOW_SECONDS)
    return count


async def is_quota_exceeded(provider_name: str, requests_per_minute: int) -> bool:
    count = await redis_client.get(_minute_key(provider_name))
    return int(count or 0) >= requests_per_minute
