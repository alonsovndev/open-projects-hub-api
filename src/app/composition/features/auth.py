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
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.composition.infrastructure import get_database_session, get_email_sender, get_jwt_handler
from src.app.composition.repositories import get_user_repository
from src.app.config.app_config import AppConfig
from src.app.features.auth.application.use_cases.confirm_password_reset import ConfirmPasswordResetUseCase
from src.app.features.auth.application.use_cases.login_user import LoginUserUseCase
from src.app.features.auth.application.use_cases.logout_user import LogoutUseCase
from src.app.features.auth.application.use_cases.refresh_token import RefreshTokenUseCase
from src.app.features.auth.application.use_cases.register_user import RegisterUserUseCase
from src.app.features.auth.application.use_cases.request_password_reset import RequestPasswordResetUseCase
from src.app.features.auth.application.use_cases.resend_reset_code import ResendResetCodeUseCase
from src.app.features.auth.application.use_cases.revoke_all_user_tokens import RevokeAllUserTokensUseCase
from src.app.features.auth.domain.repositories.password_reset_code_repository import PasswordResetCodeRepository
from src.app.features.auth.infrastructure.repositories.password_reset_code_repository_impl import (
    PasswordResetCodeRepositoryImpl,
)
from src.app.features.auth.infrastructure.repositories.sql_account_lockout_repository import SqlAccountLockoutRepository
from src.app.features.auth.infrastructure.repositories.sql_token_revocation_repository import (
    SqlTokenRevocationRepository,
)
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.infrastructure.email.email_sender import EmailSender
from src.app.shared.infrastructure.security.account_lockout_service import (
    AccountLockoutService,
    get_account_lockout_service,
)
from src.app.shared.infrastructure.security.token_revocation_service import (
    TokenRevocationService,
    get_token_revocation_service,
)


def _persist_session_state() -> bool:
    """
    Whether lockout/refresh-token state should be backed by Postgres.

    True everywhere except the `test` config profile, where unit/presentation
    tests mock repositories directly and shouldn't need a live database for
    an incidental lockout check (see config_test.yml's `auth.persist_session_state`).
    """
    return bool(AppConfig.instance().get_config("auth.persist_session_state", True))


# Use case factories
async def get_login_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
    session: AsyncSession = Depends(get_database_session),
) -> LoginUserUseCase:
    """LoginUserUseCase factory."""
    jwt_handler = get_jwt_handler()
    lockout_service = (
        AccountLockoutService(SqlAccountLockoutRepository(session))
        if _persist_session_state()
        else get_account_lockout_service()  # shared in-memory singleton — state must survive across requests
    )
    return LoginUserUseCase(user_repository, jwt_handler, lockout_service)


async def get_register_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> RegisterUserUseCase:
    """RegisterUserUseCase factory."""
    jwt_handler = get_jwt_handler()
    return RegisterUserUseCase(user_repository, jwt_handler)


async def get_refresh_token_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
    session: AsyncSession = Depends(get_database_session),
) -> RefreshTokenUseCase:
    """RefreshTokenUseCase factory."""
    jwt_handler = get_jwt_handler()
    token_revocation = (
        TokenRevocationService(SqlTokenRevocationRepository(session))
        if _persist_session_state()
        else get_token_revocation_service()  # shared in-memory singleton — state must survive across requests
    )
    return RefreshTokenUseCase(user_repository, jwt_handler, token_revocation)


async def get_logout_use_case(
    session: AsyncSession = Depends(get_database_session),
) -> LogoutUseCase:
    """LogoutUseCase factory."""
    jwt_handler = get_jwt_handler()
    token_revocation = (
        TokenRevocationService(SqlTokenRevocationRepository(session))
        if _persist_session_state()
        else get_token_revocation_service()  # shared in-memory singleton — state must survive across requests
    )
    return LogoutUseCase(jwt_handler, token_revocation)


async def get_reset_code_repository(
    session: AsyncSession = Depends(get_database_session),
) -> PasswordResetCodeRepository:
    """PasswordResetCodeRepository factory (auth-feature-specific, not shared)."""
    return PasswordResetCodeRepositoryImpl(session)


async def get_revoke_all_user_tokens_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> RevokeAllUserTokensUseCase:
    """RevokeAllUserTokensUseCase factory."""
    return RevokeAllUserTokensUseCase(user_repository)


async def get_request_password_reset_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
    reset_code_repository: PasswordResetCodeRepository = Depends(get_reset_code_repository),
    email_sender: EmailSender = Depends(get_email_sender),
) -> RequestPasswordResetUseCase:
    """RequestPasswordResetUseCase factory."""
    return RequestPasswordResetUseCase(user_repository, reset_code_repository, email_sender)


async def get_resend_reset_code_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
    reset_code_repository: PasswordResetCodeRepository = Depends(get_reset_code_repository),
    email_sender: EmailSender = Depends(get_email_sender),
) -> ResendResetCodeUseCase:
    """ResendResetCodeUseCase factory."""
    return ResendResetCodeUseCase(user_repository, reset_code_repository, email_sender)


async def get_confirm_password_reset_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
    reset_code_repository: PasswordResetCodeRepository = Depends(get_reset_code_repository),
    revoke_all_tokens_use_case: RevokeAllUserTokensUseCase = Depends(get_revoke_all_user_tokens_use_case),
) -> ConfirmPasswordResetUseCase:
    """ConfirmPasswordResetUseCase factory."""
    return ConfirmPasswordResetUseCase(user_repository, reset_code_repository, revoke_all_tokens_use_case)
