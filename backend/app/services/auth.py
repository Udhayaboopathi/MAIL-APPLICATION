from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_token, create_totp_secret, decrypt_value, encrypt_value, hash_password, verify_password, verify_totp_code
from app.deps import RequestContext, record_login_activity, verify_refresh_session
from app.models import PasswordResetToken, Session, TOTPSecret, User
from app.schemas import LoginRequest, RefreshRequest, TokenPair


async def authenticate_user(db: AsyncSession, login: LoginRequest, context: RequestContext) -> TokenPair:
    settings = get_settings()
    result = await db.execute(select(User).where(User.email == login.email))
    user = result.scalar_one_or_none()
    if not user or not user.is_active or not verify_password(login.password, user.password_hash):
        if user:
            await record_login_activity(db, user=user, context=context, success=False)
            await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user.last_login_at = datetime.now(timezone.utc)
    await record_login_activity(db, user=user, context=context, success=True)

    access_token = create_token(str(user.id))
    refresh_token = create_token(str(user.id), refresh=True)
    access_payload = __import__("app.core.security", fromlist=["decode_token"]).decode_token(access_token)
    refresh_payload = __import__("app.core.security", fromlist=["decode_token"]).decode_token(refresh_token, refresh=True)
    db.add(Session(
        user_id=user.id,
        tenant_id=user.tenant_id,
        access_jti=access_payload["jti"],
        refresh_jti=refresh_payload["jti"],
        refresh_token_hash=sha256(refresh_token.encode("utf-8")).hexdigest(),
        user_agent=context.user_agent,
        ip_address=context.ip_address,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_days),
    ))
    await db.commit()
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


async def refresh_tokens(db: AsyncSession, refresh_request: RefreshRequest) -> TokenPair:
    from app.core.security import decode_token

    payload = decode_token(refresh_request.refresh_token, refresh=True)
    result = await db.execute(select(User).where(User.id == payload.get("sub")))
    user = result.scalar_one_or_none()
    if not user or not await verify_refresh_session(db, user, refresh_request.refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    return TokenPair(
        access_token=create_token(str(user.id)),
        refresh_token=create_token(str(user.id), refresh=True),
    )


async def logout_session(db: AsyncSession, refresh_token: str) -> None:
    payload = __import__("app.core.security", fromlist=["decode_token"]).decode_token(refresh_token, refresh=True)
    result = await db.execute(select(Session).where(Session.refresh_jti == payload.get("jti")))
    session = result.scalar_one_or_none()
    if session:
        session.revoked_at = datetime.now(timezone.utc)
        await db.commit()


async def request_password_reset(db: AsyncSession, email: str) -> str:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return "accepted"
    token = token_urlsafe(32)
    db.add(PasswordResetToken(
        user_id=user.id,
        token_hash=sha256(token.encode("utf-8")).hexdigest(),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    ))
    await db.commit()
    return token


async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
    token_hash = sha256(token.encode("utf-8")).hexdigest()
    result = await db.execute(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash, PasswordResetToken.used_at.is_(None), PasswordResetToken.expires_at > datetime.now(timezone.utc)))
    reset_token = result.scalar_one_or_none()
    if not reset_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token")
    user_result = await db.execute(select(User).where(User.id == reset_token.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.password_hash = hash_password(new_password)
    reset_token.used_at = datetime.now(timezone.utc)
    await db.commit()


async def setup_totp(db: AsyncSession, user: User) -> dict:
    secret, uri = create_totp_secret()
    result = await db.execute(select(TOTPSecret).where(TOTPSecret.user_id == user.id))
    existing = result.scalar_one_or_none()
    if existing:
        existing.secret_encrypted = encrypt_value(secret)
        existing.is_enabled = False
    else:
        db.add(TOTPSecret(user_id=user.id, tenant_id=user.tenant_id, secret_encrypted=encrypt_value(secret), is_enabled=False))
    await db.commit()
    return {"secret": secret, "provisioning_uri": uri}


async def verify_totp(db: AsyncSession, user: User, code: str) -> bool:
    result = await db.execute(select(TOTPSecret).where(TOTPSecret.user_id == user.id))
    totp = result.scalar_one_or_none()
    if not totp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TOTP not configured")
    secret = decrypt_value(totp.secret_encrypted)
    ok = verify_totp_code(secret, code)
    if ok:
        totp.is_enabled = True
        totp.verified_at = datetime.now(timezone.utc)
        await db.commit()
    return ok


def create_password_hash(password: str) -> str:
    return hash_password(password)
