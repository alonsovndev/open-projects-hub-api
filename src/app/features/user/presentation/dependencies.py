from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.user.application.use_cases.change_password import ChangePasswordUseCase
from src.app.features.user.application.use_cases.create_user import CreateUserUseCase
from src.app.features.user.application.use_cases.get_user_by_id import GetUserByIdUseCase
from src.app.features.user.application.use_cases.get_user_preferences import GetUserPreferencesUseCase
from src.app.features.user.application.use_cases.get_user_profile import GetUserProfileUseCase
from src.app.features.user.application.use_cases.login_user import LoginUserUseCase
from src.app.features.user.application.use_cases.register_user import RegisterUserUseCase
from src.app.features.user.application.use_cases.refresh_token import RefreshTokenUseCase
from src.app.features.user.application.use_cases.update_user_preferences import UpdateUserPreferencesUseCase
from src.app.features.user.application.use_cases.update_user_profile import UpdateUserProfileUseCase
from src.app.features.user.infrastructure.repositories.user_preferences_repository_impl import UserPreferencesRepositoryImpl
from src.app.features.user.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from src.app.features.user.presentation.auth_dependencies import get_jwt_handler
from src.app.shared.presentation.dependencies import get_database_session


# Use Case Dependencies
async def get_login_use_case(
    session: AsyncSession = Depends(get_database_session),
) -> LoginUserUseCase:
    """
    Dependency to get LoginUserUseCase with injected dependencies.
    
    Directly provides the use case to controllers (no service layer).
    """
    user_repository = UserRepositoryImpl(session)
    jwt_handler = get_jwt_handler()
    return LoginUserUseCase(user_repository, jwt_handler)


async def get_create_user_use_case(
    session: AsyncSession = Depends(get_database_session),
) -> CreateUserUseCase:
    """
    Dependency to get CreateUserUseCase with injected dependencies.
    
    Directly provides the use case to controllers (no service layer).
    """
    user_repository = UserRepositoryImpl(session)
    return CreateUserUseCase(user_repository)


async def get_user_by_id_use_case(
    session: AsyncSession = Depends(get_database_session),
) -> GetUserByIdUseCase:
    """
    Dependency to get GetUserByIdUseCase with injected dependencies.
    
    Directly provides the use case to controllers (no service layer).
    """
    user_repository = UserRepositoryImpl(session)
    return GetUserByIdUseCase(user_repository)


async def get_register_use_case(
    session: AsyncSession = Depends(get_database_session),
) -> RegisterUserUseCase:
    """
    Dependency to get RegisterUserUseCase with injected dependencies.
    
    Used for public registration endpoint (no auth required).
    """
    user_repository = UserRepositoryImpl(session)
    jwt_handler = get_jwt_handler()
    return RegisterUserUseCase(user_repository, jwt_handler)


async def get_refresh_token_use_case(
    session: AsyncSession = Depends(get_database_session),
) -> RefreshTokenUseCase:
    """
    Dependency to get RefreshTokenUseCase with injected dependencies.
    
    Used for token refresh endpoint (public, but requires valid refresh token).
    """
    user_repository = UserRepositoryImpl(session)
    jwt_handler = get_jwt_handler()
    return RefreshTokenUseCase(user_repository, jwt_handler)


async def get_user_profile_use_case(
    session: AsyncSession = Depends(get_database_session),
) -> GetUserProfileUseCase:
    """
    Dependency to get GetUserProfileUseCase with injected dependencies.
    
    Used for authenticated user profile retrieval.
    """
    user_repository = UserRepositoryImpl(session)
    return GetUserProfileUseCase(user_repository)


async def get_update_user_profile_use_case(
    session: AsyncSession = Depends(get_database_session),
) -> UpdateUserProfileUseCase:
    """
    Dependency to get UpdateUserProfileUseCase with injected dependencies.
    
    Used for authenticated user profile updates.
    """
    user_repository = UserRepositoryImpl(session)
    return UpdateUserProfileUseCase(user_repository)


async def get_change_password_use_case(
    session: AsyncSession = Depends(get_database_session),
) -> ChangePasswordUseCase:
    """
    Dependency to get ChangePasswordUseCase with injected dependencies.
    
    Used for authenticated user password changes.
    """
    user_repository = UserRepositoryImpl(session)
    return ChangePasswordUseCase(user_repository)


async def get_user_preferences_use_case(
    session: AsyncSession = Depends(get_database_session),
) -> GetUserPreferencesUseCase:
    """
    Dependency to get GetUserPreferencesUseCase with injected dependencies.
    
    Used for authenticated user preferences retrieval (creates default if not found).
    """
    preferences_repository = UserPreferencesRepositoryImpl(session)
    return GetUserPreferencesUseCase(preferences_repository)


async def get_update_user_preferences_use_case(
    session: AsyncSession = Depends(get_database_session),
) -> UpdateUserPreferencesUseCase:
    """
    Dependency to get UpdateUserPreferencesUseCase with injected dependencies.
    
    Used for authenticated user preferences updates (partial update support).
    """
    preferences_repository = UserPreferencesRepositoryImpl(session)
    return UpdateUserPreferencesUseCase(preferences_repository)
