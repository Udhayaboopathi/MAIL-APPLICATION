#!/usr/bin/env python
"""Create super admin user in the database."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import engine, async_session_factory
from app.models import Base, User


async def create_admin():
    """Create super admin user."""
    settings = get_settings()
    
    # Debug: Check password value
    admin_password = settings.admin_password
    print(f"Password from config: '{admin_password}'")
    print(f"Password length (chars): {len(admin_password)}")
    print(f"Password length (bytes): {len(admin_password.encode())}")
    
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with async_session_factory() as session:
        # Check if admin already exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.email == "admin@sudoinnovation.tech")
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print("✓ Admin user already exists")
            return
        
        # Create admin user
        admin_password = settings.admin_password
        # Truncate to 72 bytes (bcrypt limit)
        password_bytes = admin_password.encode()
        if len(password_bytes) > 72:
            admin_password = password_bytes[:72].decode('utf-8', errors='ignore')
            print(f"⚠ Password truncated to 72 bytes for bcrypt compatibility")
        
        print(f"Password to hash (chars): {len(admin_password)}")
        print(f"Password to hash (bytes): {len(admin_password.encode())}")
        
        hashed_password = hash_password(admin_password)
        
        admin_user = User(
            email="admin@sudoinnovation.tech",
            password_hash=hashed_password,
            full_name="Super Admin",
            role="SUPER_ADMIN",
            is_active=True,
        )
        
        session.add(admin_user)
        await session.commit()
        
        print("✓ Super admin created successfully")
        print(f"  Email: admin@sudoinnovation.tech")
        print(f"  Password: {settings.admin_password}")


if __name__ == "__main__":
    asyncio.run(create_admin())
