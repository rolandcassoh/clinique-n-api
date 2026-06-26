from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from app.config import settings

# Pool de connexions Redis (singleton)
_pool: aioredis.Redis | None = None


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Retourne la connexion Redis partagée (pool unique)."""
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(settings.redis_url, decode_responses=True)
    yield _pool


async def close_redis() -> None:
    """Ferme proprement le pool de connexions Redis."""
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None
