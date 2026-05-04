from __future__ import annotations

import asyncio
from typing import Optional

from redis.asyncio import Redis

from app.core.config import get_settings


_settings = get_settings()

# Create a Redis client instance lazily to avoid startup ordering issues.
_redis_client: Optional[Redis] = None


def get_redis() -> Redis:
    """Return a singleton Redis client. The client is created lazily.

    Use `await get_redis().ping()` to check connectivity. This wrapper centralizes
    where the Redis URL is read from and allows future changes (pooling, SSL).
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(_settings.redis_url, decode_responses=True)
    return _redis_client


async def ensure_redis_ready(timeout: int = 5) -> bool:
    client = get_redis()
    try:
        await asyncio.wait_for(client.ping(), timeout=timeout)
        return True
    except Exception:
        return False
