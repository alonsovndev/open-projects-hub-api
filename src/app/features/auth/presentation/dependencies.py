"""Dependency injection for auth feature."""
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.auth.application.use_cases.login_user import LoginUserUseCase
from src.app.features.auth.application.use_cases.register_user import RegisterUserUseCase
from src.app.features.auth.application.use_cases.refresh_token import RefreshTokenUseCase
from src.app.features.auth.presentation.auth_dependencies import get_jwt_handler
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.features.user.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from src.app.shared.persistence.db_session import get_database_session


async def get_user_repository(
    session: AsyncSession = Depends(get_database_session),
) -> UserRepository:
    """Get user repository instance."""
    return UserRepositoryImpl(session)


async def get_login_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> LoginUserUseCase:
    """Get LoginUserUseCase instance."""
    jwt_handler = get_jwt_handler()
    return LoginUserUseCase(user_repository, jwt_handler)


async def get_register_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> RegisterUserUseCase:
    """Get RegisterUserUseCase instance."""
    jwt_handler = get_jwt_handler()
    return RegisterUserUseCase(user_repository, jwt_handler)


async def get_refresh_token_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> RefreshTokenUseCase:
    """Get RefreshTokenUseCase instance."""
    jwt_handler = get_jwt_handler()
    return RefreshTokenUseCase(user_repository, jwt_handler)
