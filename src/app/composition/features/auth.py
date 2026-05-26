"""
Auth feature dependency composition.

All dependency wiring for authentication use cases.

Dependencies:
- Infrastructure: Database session
- Repositories: UserRepository (shared)
- Services: JWT handler (from auth_dependencies)

Use Cases:
- Login: Authenticate user credentials
- Register: Create new user account
- Refresh Token: Issue new access/refresh token pair

Usage:
    from src.app.composition import get_login_use_case

    @router.post("/login")
    async def login(
        use_case: LoginUseCase = Depends(get_login_use_case),
    ):
        return await use_case.execute(...)
"""

from fastapi import Depends

from src.app.composition.repositories import get_user_repository
from src.app.features.auth.application.use_cases.login_user import LoginUserUseCase
from src.app.features.auth.application.use_cases.refresh_token import RefreshTokenUseCase
from src.app.features.auth.application.use_cases.register_user import RegisterUserUseCase
from src.app.features.auth.presentation.auth_dependencies import get_jwt_handler
from src.app.features.user.domain.repositories.user_repository import UserRepository


# Use case factories
async def get_login_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> LoginUserUseCase:
    """LoginUserUseCase factory."""
    jwt_handler = get_jwt_handler()
    return LoginUserUseCase(user_repository, jwt_handler)


async def get_register_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> RegisterUserUseCase:
    """RegisterUserUseCase factory."""
    jwt_handler = get_jwt_handler()
    return RegisterUserUseCase(user_repository, jwt_handler)


async def get_refresh_token_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> RefreshTokenUseCase:
    """RefreshTokenUseCase factory."""
    jwt_handler = get_jwt_handler()
    return RefreshTokenUseCase(user_repository, jwt_handler)
