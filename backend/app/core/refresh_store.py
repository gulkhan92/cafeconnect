import uuid

from app.core.config import settings
from app.core.redis import redis_client


def _key(user_id: uuid.UUID | str, jti: str) -> str:
    return f"refresh:{user_id}:{jti}"


async def store_refresh_token(user_id: uuid.UUID, jti: str) -> None:
    ttl_seconds = settings.refresh_token_expire_days * 24 * 60 * 60
    await redis_client.set(_key(user_id, jti), "1", ex=ttl_seconds)


async def is_refresh_token_active(user_id: uuid.UUID | str, jti: str) -> bool:
    return bool(await redis_client.exists(_key(user_id, jti)))


async def revoke_refresh_token(user_id: uuid.UUID | str, jti: str) -> None:
    await redis_client.delete(_key(user_id, jti))
