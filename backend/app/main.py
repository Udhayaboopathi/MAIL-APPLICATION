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
    import subprocess

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

    # Run Alembic migrations
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd="/app",
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            print(f"Warning: Alembic migrations failed: {result.stderr}")
        else:
            print("Alembic migrations completed successfully")
    except Exception as e:
        print(f"Warning: Could not run Alembic migrations: {e}")

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

    # Auto-create a super-admin if ADMIN_PASSWORD is provided, or in non-production environments
    admin_email = "admin@sudoinnovation.tech"
    admin_password = settings.admin_password
    
    if admin_password or settings.environment != "production":
        async with async_session_factory() as session:
            # Check if admin already exists
            result = await session.execute(text(f"SELECT id FROM users WHERE email = '{admin_email}' LIMIT 1"))
            existing_admin = result.first()
            
            if not existing_admin:
                import secrets
                import os

                # Use provided password or generate one
                raw_password = admin_password or secrets.token_urlsafe(16)
                # Bcrypt has a 72-byte limit for passwords - safely truncate to 60 chars to handle UTF-8
                raw_password_for_hash = raw_password[:60]
                
                try:
                    user = User(email=admin_email, password_hash=hash_password(raw_password_for_hash), role="SUPER_ADMIN")
                    session.add(user)
                    await session.commit()
                    
                    # Log the credentials (use truncated version that was hashed)
                    try:
                        out_path = os.environ.get("INITIAL_ADMIN_OUTPUT", "/tmp/initial_super_admin.txt")
                        with open(out_path, "w", encoding="utf-8") as fh:
                            fh.write(f"email={admin_email}\npassword={raw_password_for_hash}\n")
                    except Exception:
                        print("Super admin created:", admin_email)
                        print("Password:", raw_password_for_hash)
                        if not admin_password:
                            print("Generated password (store this safely):", raw_password_for_hash)
                except Exception as e:
                    print(f"Warning: Could not create super admin: {e}")


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
