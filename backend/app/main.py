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

# Configure CORS origins from settings to avoid hard-coded domains
allowed_origins = ["http://localhost:3000"]
if settings.next_public_api_base_url:
    allowed_origins.append(str(settings.next_public_api_base_url))
allowed_origins.append(f"https://{settings.domain}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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

    # Basic runtime checks for secrets before allowing production startup
    if settings.environment == "production":
        problems: list[str] = []
        if not settings.jwt_secret_key or len(settings.jwt_secret_key) < 32:
            problems.append("JWT_SECRET is missing or too short (min 32 chars)")
        if not settings.jwt_refresh_secret_key or len(settings.jwt_refresh_secret_key) < 32:
            problems.append("JWT_REFRESH_SECRET is missing or too short (min 32 chars)")
        if not settings.encryption_key or len(settings.encryption_key) < 32:
            problems.append("ENCRYPTION_KEY is missing or too short (min 32 chars)")
        if problems:
            raise RuntimeError("Startup secret checks failed: " + "; ".join(problems))

    # Auto-create a super-admin only in non-production environments. For production,
    # administrators should be provisioned via a secure onboarding process.
    if settings.environment != "production":
        async with async_session_factory() as session:
            result = await session.execute(text("SELECT count(1) as cnt FROM users"))
            row = result.first()
            count = int(row[0]) if row else 0
            if count == 0:
                import secrets
                import os

                email = f"admin@{settings.domain}"
                raw_password = secrets.token_urlsafe(16)
                user = User(email=email, password_hash=hash_password(raw_password), role="SUPER_ADMIN")
                session.add(user)
                await session.commit()
                # Persist the generated credentials to a file with restrictive permissions so
                # container owners can retrieve them without exposing them in logs.
                try:
                    out_path = os.environ.get("INITIAL_ADMIN_OUTPUT", "/tmp/initial_super_admin.txt")
                    with open(out_path, "w", encoding="utf-8") as fh:
                        fh.write(f"email={email}\npassword={raw_password}\n")
                except Exception:
                    # If writing fails, fall back to printing to stdout only in non-production.
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
