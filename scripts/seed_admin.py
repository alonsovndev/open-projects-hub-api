#!/usr/bin/env python3
"""
Database seed script to create the first admin user.

Usage:
    python scripts/seed_admin.py

Environment variables:
    ADMIN_EMAIL: Email for the admin user (default: admin@example.com)
    ADMIN_PASSWORD: Password for the admin user (default: Admin123!@#)
    ADMIN_DISPLAY_NAME: Display name for the admin (default: System Administrator)
    DATABASE_URL: PostgreSQL connection string (required)

Example:
    ADMIN_EMAIL="admin@mycompany.com" \
    ADMIN_PASSWORD="SecurePass123!" \
    ADMIN_DISPLAY_NAME="Main Admin" \
    DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/dbname" \
    python scripts/seed_admin.py
"""

import asyncio
import os
import sys
from pathlib import Path


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.email import Email
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.features.user.infrastructure.models.user_model import UserModel
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.security.password_handler import PasswordHandler


async def seed_admin():
    """Create the first admin user if it doesn't exist."""

    # Get configuration from environment
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com").lower().strip()
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin123!@#")
    admin_display_name = os.getenv("ADMIN_DISPLAY_NAME", "System Administrator")
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable is required")
        print("Example: postgresql+asyncpg://user:pass@localhost:5432/dbname")
        sys.exit(1)

    # Validate password complexity
    if len(admin_password) < 8:
        print("❌ ERROR: Admin password must be at least 8 characters long")
        sys.exit(1)

    print("=" * 60)
    print("🌱 Admin User Seed Script")
    print("=" * 60)
    print(f"Database: {database_url.split('@')[-1]}")  # Hide credentials in output
    print(f"Admin Email: {admin_email}")
    print(f"Admin Name: {admin_display_name}")
    print("-" * 60)

    # Create async engine and session
    engine = create_async_engine(database_url, echo=False)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        try:
            # Check if admin already exists
            from sqlalchemy import select

            stmt = select(UserModel).where(UserModel.email == admin_email)
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(f"⚠️  Admin user already exists: {admin_email}")
                print(f"   User ID: {existing_user.id}")
                print(f"   Role: {existing_user.role}")
                print(f"   Created: {existing_user.created_at}")
                print("-" * 60)
                print("✅ No action needed - admin user already exists")
                return

            # Hash password
            password_hash = await PasswordHandler.hash_password(admin_password)

            # Create admin user entity
            admin_entity = UserEntity(
                id=EntityId.from_string(str(uuid4())),
                email=Email(admin_email),
                display_name=admin_display_name,
                password_hash=password_hash,
                role=UserRole.ADMIN,
            )

            # Create database model
            admin_model = UserModel(
                id=admin_entity.id.value,
                email=admin_entity.email.value,
                display_name=admin_entity.display_name,
                password_hash=admin_entity.password_hash,
                role=admin_entity.role.value,  # 'admin' string value
            )

            # Save to database
            session.add(admin_model)
            await session.commit()
            await session.refresh(admin_model)

            print("✅ Admin user created successfully!")
            print(f"   User ID: {admin_model.id}")
            print(f"   Email: {admin_model.email}")
            print(f"   Display Name: {admin_model.display_name}")
            print(f"   Role: {admin_model.role}")
            print(f"   Created At: {admin_model.created_at}")
            print("=" * 60)
            print("🎉 You can now login with these credentials:")
            print(f"   Email: {admin_email}")
            print(f"   Password: {admin_password}")
            print("=" * 60)

        except Exception as e:
            print("❌ ERROR: Failed to create admin user")
            print(f"   {type(e).__name__}: {e!s}")
            await session.rollback()
            sys.exit(1)
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_admin())
