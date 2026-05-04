from __future__ import annotations

import json
from typing import Any

from app.core.redis import get_redis


redis_client = get_redis()


async def incr_rate_limit(key: str, ttl_seconds: int) -> int:
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, ttl_seconds)
    return count


async def set_json(key: str, value: Any, ttl_seconds: int | None = None) -> None:
    payload = json.dumps(value)
    await redis_client.set(key, payload, ex=ttl_seconds)


async def get_json(key: str) -> Any:
    raw = await redis_client.get(key)
    return json.loads(raw) if raw else None


async def publish_event(stream: str, payload: dict[str, Any]) -> None:
    await redis_client.xadd(stream, payload)
