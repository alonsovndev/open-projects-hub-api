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
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.features.user.domain.repositories.user_preferences_repository import UserPreferencesRepository
from src.app.features.user.infrastructure.repositories.user_preferences_repository_impl import UserPreferencesRepositoryImpl
from src.app.features.user.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from src.app.features.user.presentation.auth_dependencies import get_jwt_handler
from src.app.shared.presentation.dependencies import get_database_session


# Repository factories
async def get_user_repository(
    session: AsyncSession = Depends(get_database_session),
) -> UserRepository:
    """
    Get user repository instance.
    
    Args:
        session: Database session
        
    Returns:
        UserRepository instance
    """
    return UserRepositoryImpl(session)


async def get_user_preferences_repository(
    session: AsyncSession = Depends(get_database_session),
) -> UserPreferencesRepository:
    """
    Get user preferences repository instance.
    
    Args:
        session: Database session
        
    Returns:
        UserPreferencesRepository instance
    """
    return UserPreferencesRepositoryImpl(session)


# Use Case Dependencies
async def get_login_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> LoginUserUseCase:
    """
    Dependency to get LoginUserUseCase with injected dependencies.
    
    Directly provides the use case to controllers (no service layer).
    """
    jwt_handler = get_jwt_handler()
    return LoginUserUseCase(user_repository, jwt_handler)


async def get_create_user_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> CreateUserUseCase:
    """
    Dependency to get CreateUserUseCase with injected dependencies.
    
    Directly provides the use case to controllers (no service layer).
    """
    return CreateUserUseCase(user_repository)


async def get_user_by_id_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> GetUserByIdUseCase:
    """
    Dependency to get GetUserByIdUseCase with injected dependencies.
    
    Directly provides the use case to controllers (no service layer).
    """
    return GetUserByIdUseCase(user_repository)


async def get_register_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> RegisterUserUseCase:
    """
    Dependency to get RegisterUserUseCase with injected dependencies.
    
    Used for public registration endpoint (no auth required).
    """
    jwt_handler = get_jwt_handler()
    return RegisterUserUseCase(user_repository, jwt_handler)


async def get_refresh_token_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> RefreshTokenUseCase:
    """
    Dependency to get RefreshTokenUseCase with injected dependencies.
    
    Used for token refresh endpoint (public, but requires valid refresh token).
    """
    jwt_handler = get_jwt_handler()
    return RefreshTokenUseCase(user_repository, jwt_handler)


async def get_user_profile_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> GetUserProfileUseCase:
    """
    Dependency to get GetUserProfileUseCase with injected dependencies.
    
    Used for authenticated user profile retrieval.
    """
    return GetUserProfileUseCase(user_repository)


async def get_update_user_profile_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> UpdateUserProfileUseCase:
    """
    Dependency to get UpdateUserProfileUseCase with injected dependencies.
    
    Used for authenticated user profile updates.
    """
    return UpdateUserProfileUseCase(user_repository)


async def get_change_password_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> ChangePasswordUseCase:
    """
    Dependency to get ChangePasswordUseCase with injected dependencies.
    
    Used for authenticated user password changes.
    """
    return ChangePasswordUseCase(user_repository)


async def get_user_preferences_use_case(
    preferences_repository: UserPreferencesRepository = Depends(get_user_preferences_repository),
) -> GetUserPreferencesUseCase:
    """
    Dependency to get GetUserPreferencesUseCase with injected dependencies.
    
    Used for authenticated user preferences retrieval (creates default if not found).
    """
    return GetUserPreferencesUseCase(preferences_repository)


async def get_update_user_preferences_use_case(
    preferences_repository: UserPreferencesRepository = Depends(get_user_preferences_repository),
) -> UpdateUserPreferencesUseCase:
    """
    Dependency to get UpdateUserPreferencesUseCase with injected dependencies.
    
    Used for authenticated user preferences updates (partial update support).
    """
    return UpdateUserPreferencesUseCase(preferences_repository)
