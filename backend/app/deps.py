from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token, verify_password
from app.db.session import get_db
from app.models import ApiKey, LoginActivity, Session, User


@dataclass(slots=True)
class RequestContext:
    ip_address: str | None
    user_agent: str | None


async def get_request_context(request: Request) -> RequestContext:
    forwarded = request.headers.get("x-forwarded-for")
    ip_address = forwarded.split(",")[0].strip() if forwarded else request.client.host if request.client else None
    return RequestContext(ip_address=ip_address, user_agent=request.headers.get("user-agent"))


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_token(token)
    except Exception as exc:  # pragma: no cover - token decode is intentionally defensive
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    return user


def require_role(*allowed_roles: str):
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles and current_user.role != "SUPER_ADMIN":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return current_user

    return dependency


async def get_current_api_key(
    db: AsyncSession = Depends(get_db),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> ApiKey:
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")
    key_hash = sha256(x_api_key.encode("utf-8")).hexdigest()
    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_enabled.is_(True)))
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    api_key.last_used_at = datetime.now(timezone.utc)
    return api_key


async def record_login_activity(
    db: AsyncSession,
    *,
    user: User,
    context: RequestContext,
    success: bool,
) -> None:
    db.add(LoginActivity(
        tenant_id=user.tenant_id,
        user_id=user.id,
        ip_address=context.ip_address,
        device=context.user_agent,
        user_agent=context.user_agent,
        success=success,
    ))


async def verify_refresh_session(db: AsyncSession, user: User, refresh_token: str) -> bool:
    token_hash = sha256(refresh_token.encode("utf-8")).hexdigest()
    result = await db.execute(
        select(Session).where(
            Session.user_id == user.id,
            Session.refresh_token_hash == token_hash,
            Session.revoked_at.is_(None),
            Session.expires_at > datetime.now(timezone.utc),
        )
    )
    token = result.scalar_one_or_none()
    return token is not None
