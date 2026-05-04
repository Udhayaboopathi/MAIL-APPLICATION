from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.fernet import Fernet
from jose import jwt
from passlib.context import CryptContext
import pyotp

from app.core.config import get_settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_token(subject: str, *, refresh: bool = False, extra_claims: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    expires_delta = timedelta(days=settings.jwt_refresh_token_days) if refresh else timedelta(minutes=settings.jwt_access_token_minutes)
    expire = datetime.now(timezone.utc) + expires_delta
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "type": "refresh" if refresh else "access",
        "jti": secrets.token_urlsafe(16),
    }
    if extra_claims:
        payload.update(extra_claims)
    secret = settings.jwt_refresh_secret_key if refresh else settings.jwt_secret_key
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str, *, refresh: bool = False) -> dict[str, Any]:
    settings = get_settings()
    secret = settings.jwt_refresh_secret_key if refresh else settings.jwt_secret_key
    return jwt.decode(token, secret, algorithms=["HS256"])


def generate_api_key() -> tuple[str, str, str]:
    raw_key = f"nexudo_sk_{secrets.token_urlsafe(32)}"
    prefix = raw_key[:16]
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return raw_key, prefix, key_hash


def _fernet() -> Fernet:
    settings = get_settings()
    derived_key = base64.urlsafe_b64encode(hashlib.sha256(settings.encryption_key.encode("utf-8")).digest())
    return Fernet(derived_key)


def encrypt_value(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(value: str) -> str:
    return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")


def create_totp_secret() -> tuple[str, str]:
    secret = pyotp.random_base32()
    provisioning_uri = pyotp.TOTP(secret).provisioning_uri(name=f"nexudo@nexudo.dev", issuer_name="Nexudo Mail")
    return secret, provisioning_uri


def verify_totp_code(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code, valid_window=1)
