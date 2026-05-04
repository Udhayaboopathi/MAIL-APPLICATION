from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1 import router as v1_router
from app.core.config import get_settings
from app.core.redis import ensure_redis_ready
from app.db.session import async_session_factory, engine
from app.core.security import hash_password
from app.models import User


settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://nexudo.dev"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
async def on_startup() -> None:
    # Try to connect to DB with a few retries (useful when PgBouncer/postgres start later)
    import asyncio

    retries = 6
    for attempt in range(1, retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            break
        except Exception:
            if attempt == retries:
                raise
            await asyncio.sleep(2 * attempt)

    # Ensure Redis is ready
    await ensure_redis_ready()

    # Auto-create a super-admin if no users exist. A random password is generated and printed
    # to stdout (check container logs). This avoids keeping ADMIN_PASS in .env.
    async with async_session_factory() as session:
        result = await session.execute(text("SELECT count(1) as cnt FROM users"))
        row = result.first()
        count = int(row[0]) if row else 0
        if count == 0:
            import secrets

            email = f"admin@{settings.domain}"
            raw_password = secrets.token_urlsafe(16)
            user = User(email=email, password_hash=hash_password(raw_password), role="SUPER_ADMIN")
            session.add(user)
            await session.commit()
            print("Super admin created:", email)
            print("Generated password (store this safely):", raw_password)


@app.get("/health")
async def health() -> dict[str, str]:
    # Health checks: DB + Redis
    db_ok = False
    redis_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        db_ok = False
    try:
        redis_ok = await ensure_redis_ready()
    except Exception:
        redis_ok = False
    status = "ok" if db_ok and redis_ok else "degraded"
    return {"status": status, "db": "ok" if db_ok else "fail", "redis": "ok" if redis_ok else "fail"}
