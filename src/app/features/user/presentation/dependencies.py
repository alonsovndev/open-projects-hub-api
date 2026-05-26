from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.user.application.use_cases.change_password import ChangePasswordUseCase
from src.app.features.user.application.use_cases.create_user import CreateUserUseCase
from src.app.features.user.application.use_cases.get_user_by_id import GetUserByIdUseCase
from src.app.features.user.application.use_cases.get_user_preferences import GetUserPreferencesUseCase
from src.app.features.user.application.use_cases.get_user_profile import GetUserProfileUseCase
from src.app.features.user.application.use_cases.update_user_preferences import UpdateUserPreferencesUseCase
from src.app.features.user.application.use_cases.update_user_profile import UpdateUserProfileUseCase
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.features.user.domain.repositories.user_preferences_repository import UserPreferencesRepository
from src.app.features.user.infrastructure.repositories.user_preferences_repository_impl import UserPreferencesRepositoryImpl
from src.app.features.user.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from src.app.shared.persistence.db_session import get_database_session


# Repository factories
async def get_user_repository(
    session: AsyncSession = Depends(get_database_session),
) -> UserRepository:
    """Get user repository instance."""
    return UserRepositoryImpl(session)


async def get_user_preferences_repository(
    session: AsyncSession = Depends(get_database_session),
) -> UserPreferencesRepository:
    """Get user preferences repository instance."""
    return UserPreferencesRepositoryImpl(session)


# Use Case Dependencies
async def get_create_user_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> CreateUserUseCase:
    """Get CreateUserUseCase instance."""
    return CreateUserUseCase(user_repository)


async def get_user_by_id_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> GetUserByIdUseCase:
    """Get GetUserByIdUseCase instance."""
    return GetUserByIdUseCase(user_repository)


async def get_user_profile_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> GetUserProfileUseCase:
    """Get GetUserProfileUseCase instance."""
    return GetUserProfileUseCase(user_repository)


async def get_update_user_profile_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> UpdateUserProfileUseCase:
    """Get UpdateUserProfileUseCase instance."""
    return UpdateUserProfileUseCase(user_repository)


async def get_change_password_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> ChangePasswordUseCase:
    """Get ChangePasswordUseCase instance."""
    return ChangePasswordUseCase(user_repository)


async def get_user_preferences_use_case(
    preferences_repository: UserPreferencesRepository = Depends(get_user_preferences_repository),
) -> GetUserPreferencesUseCase:
    """Get GetUserPreferencesUseCase instance."""
    return GetUserPreferencesUseCase(preferences_repository)


async def get_update_user_preferences_use_case(
    preferences_repository: UserPreferencesRepository = Depends(get_user_preferences_repository),
) -> UpdateUserPreferencesUseCase:
    """Get UpdateUserPreferencesUseCase instance."""
    return UpdateUserPreferencesUseCase(preferences_repository)
