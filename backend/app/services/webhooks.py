from __future__ import annotations

import hmac
import hashlib

import httpx


def sign_payload(secret: str, payload: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


async def dispatch_webhook(url: str, secret: str, payload: dict) -> None:
    body = __import__("json").dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "X-Nexudo-Signature": sign_payload(secret, body)}
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, content=body, headers=headers)
        response.raise_for_status()
