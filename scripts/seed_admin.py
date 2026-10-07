#!/usr/bin/env python3
"""
Database seed script to create the first admin user.

Connects using the same configuration the running application uses
(src/app/config/config_<APP_ENV>.yml + .env), so it always targets
whatever database the app itself is configured for.

Usage:
    python scripts/seed_admin.py

Environment variables:
    APP_ENV: Application environment (local, dev, container, prod, test) - default: dev
    ADMIN_EMAIL: Email for the admin user (default: admin@example.com)
    ADMIN_PASSWORD: Password for the admin user (default: Admin123!@#)
    ADMIN_DISPLAY_NAME: Display name for the admin (default: System Administrator)

Example:
    APP_ENV="container" \
    ADMIN_EMAIL="admin@mycompany.com" \
    ADMIN_PASSWORD="SecurePass123!" \
    ADMIN_DISPLAY_NAME="Main Admin" \
    python scripts/seed_admin.py
"""

import asyncio
import os
import sys
from pathlib import Path


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app.config.app_config import AppConfig
from src.app.features.user.domain.entities.user_entity import INITIAL_AI_CREDITS, UserEntity
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.features.user.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from src.app.features.workspaces.domain.entities.workspace_entity import WorkspaceEntity
from src.app.features.workspaces.infrastructure.repositories.workspace_repository_impl import WorkspaceRepositoryImpl
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.infrastructure.security.password_handler import PasswordHandler
from src.app.shared.persistence.engine_factory import close_engine, get_engine


async def seed_admin():
    """Create the first admin user if it doesn't exist."""

    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com").lower().strip()
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin123!@#")
    admin_display_name = os.getenv("ADMIN_DISPLAY_NAME", "System Administrator")

    if len(admin_password) < 8:
        print("❌ ERROR: Admin password must be at least 8 characters long")
        sys.exit(1)

    app_env = AppConfig.instance().env

    print("=" * 60)
    print("🌱 Admin User Seed Script")
    print("=" * 60)
    print(f"App Environment: {app_env}")
    print(f"Admin Email: {admin_email}")
    print(f"Admin Name: {admin_display_name}")
    print("-" * 60)

    engine = get_engine()

    try:
        async with engine.get_session() as session:
            repository = UserRepositoryImpl(session)

            existing_user = await repository.find_by_email(Email(admin_email))

            if existing_user:
                print(f"⚠️  Admin user already exists: {admin_email}")
                print(f"   User ID: {existing_user.id}")
                print(f"   Role: {existing_user.role}")
                print(f"   Created: {existing_user.created_at}")
                print("-" * 60)
                print("✅ No action needed - admin user already exists")
                return

            password_hash = await PasswordHandler.hash_password(admin_password)

            workspace = WorkspaceEntity.create(WorkspaceEntity.default_name_for(admin_display_name))
            admin_entity = UserEntity.create(
                email=admin_email,
                display_name=admin_display_name,
                password_hash=password_hash,
                role=UserRole.ADMIN,
                workspace_id=workspace.id,
            )

            saved_user = await WorkspaceRepositoryImpl(session).create_with_admin(workspace, admin_entity)

            if saved_user is None:
                print(f"❌ ERROR: Failed to create admin user - email may already be in use: {admin_email}")
                sys.exit(1)

            # UserEntity.create grants credits directly; count them against the workspace ceiling.
            await WorkspaceRepositoryImpl(session).reserve_ai_credits(
                workspace.id, INITIAL_AI_CREDITS, INITIAL_AI_CREDITS
            )
            await session.commit()

            print("✅ Admin user created successfully!")
            print(f"   User ID: {saved_user.id}")
            print(f"   Email: {saved_user.email}")
            print(f"   Display Name: {saved_user.display_name}")
            print(f"   Role: {saved_user.role}")
            print(f"   Workspace: {workspace.name}")
            print(f"   Created At: {saved_user.created_at}")
            print("=" * 60)
            print("🎉 You can now login with these credentials:")
            print(f"   Email: {admin_email}")
            print(f"   Password: {admin_password}")
            print("=" * 60)

    except Exception as e:
        print("❌ ERROR: Failed to create admin user")
        print(f"   {type(e).__name__}: {e!s}")
        sys.exit(1)
    finally:
        await close_engine()


if __name__ == "__main__":
    asyncio.run(seed_admin())
