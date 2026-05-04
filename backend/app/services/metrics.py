from __future__ import annotations

from app.services.redis import get_json, set_json


async def increment_metric(tenant_id: str, metric: str, by: int = 1) -> int:
    key = f"metrics:{tenant_id}"
    current = await get_json(key) or {}
    current[metric] = int(current.get(metric, 0)) + by
    await set_json(key, current, ttl_seconds=86400)
    return current[metric]
