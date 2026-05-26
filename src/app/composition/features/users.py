"""
Users feature dependency composition.

All dependency wiring for user management and profile use cases.

Dependencies:
- Infrastructure: Database session
- Repositories:
  - UserRepository (shared, also used by auth and dashboard)
  - UserPreferencesRepository (feature-specific, defined here)

Use Cases:
- Create User: Admin-only user creation
- Get User by ID: Retrieve user details
- Get User Profile: Retrieve current user's profile
- Update User Profile: Modify profile information
- Get User Preferences: Retrieve user UI/notification preferences
- Update User Preferences: Modify preferences (theme, notifications, etc.)
- Change Password: Update user password with validation

Domain Separation:
- User entity: Core identity, credentials, role
- UserPreferences entity: UI settings, notification preferences
  Stored separately for performance and separation of concerns

Usage:
    from src.app.composition import get_get_user_profile_use_case

    @router.get("/profile")
    async def get_profile(
        use_case: GetUserProfileUseCase = Depends(get_get_user_profile_use_case),
    ):
        return await use_case.execute(...)
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.composition.infrastructure import get_database_session
from src.app.composition.repositories import get_user_repository
from src.app.features.user.application.use_cases.change_password import ChangePasswordUseCase
from src.app.features.user.application.use_cases.create_user import CreateUserUseCase
from src.app.features.user.application.use_cases.get_user_by_id import GetUserByIdUseCase
from src.app.features.user.application.use_cases.get_user_preferences import GetUserPreferencesUseCase
from src.app.features.user.application.use_cases.get_user_profile import GetUserProfileUseCase
from src.app.features.user.application.use_cases.update_user_preferences import UpdateUserPreferencesUseCase
from src.app.features.user.application.use_cases.update_user_profile import UpdateUserProfileUseCase
from src.app.features.user.domain.repositories.user_preferences_repository import UserPreferencesRepository
from src.app.features.user.domain.repositories.user_repository import UserRepository


# Feature-specific repository (not shared)
async def get_user_preferences_repository(
    session: AsyncSession = Depends(get_database_session),
) -> UserPreferencesRepository:
    """
    User preferences repository factory (feature-specific).

    Only used by users feature for managing UI preferences.
    Separated from UserRepository for domain separation.
    """
    from src.app.features.user.infrastructure.repositories.user_preferences_repository_impl import (
        UserPreferencesRepositoryImpl,
    )

    return UserPreferencesRepositoryImpl(session)


# Use case factories
async def get_create_user_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> CreateUserUseCase:
    """CreateUserUseCase factory."""
    return CreateUserUseCase(user_repository)


async def get_get_user_by_id_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> GetUserByIdUseCase:
    """GetUserByIdUseCase factory."""
    return GetUserByIdUseCase(user_repository)


async def get_get_user_profile_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> GetUserProfileUseCase:
    """GetUserProfileUseCase factory."""
    return GetUserProfileUseCase(user_repository)


async def get_update_user_profile_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> UpdateUserProfileUseCase:
    """UpdateUserProfileUseCase factory."""
    return UpdateUserProfileUseCase(user_repository)


async def get_change_password_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> ChangePasswordUseCase:
    """ChangePasswordUseCase factory."""
    return ChangePasswordUseCase(user_repository)


async def get_get_user_preferences_use_case(
    preferences_repository: UserPreferencesRepository = Depends(get_user_preferences_repository),
) -> GetUserPreferencesUseCase:
    """GetUserPreferencesUseCase factory."""
    return GetUserPreferencesUseCase(preferences_repository)


async def get_update_user_preferences_use_case(
    preferences_repository: UserPreferencesRepository = Depends(get_user_preferences_repository),
) -> UpdateUserPreferencesUseCase:
    """UpdateUserPreferencesUseCase factory."""
    return UpdateUserPreferencesUseCase(preferences_repository)
