"""
AI credit and API key feature dependency composition.

Dependencies:
- Infrastructure: Database session, API key cipher (singleton), platform AI service
- Repositories:
  - UserApiKeyRepository (feature-specific, defined here)
  - UserRepository (shared — the credit balance lives on the user record)

Use Cases:
- Get Credit Balance: remaining free platform refinements
- List / Save / Delete / Validate API Key: user-owned provider credentials

Security:
The cipher is an application-scoped singleton built once from the configured master key,
so a missing or malformed key fails at first use rather than silently per request. Provider
clients built from a user's key are never cached — see RefinementProviderResolver.

Usage:
    from src.app.composition import get_save_api_key_use_case

    @router.post("/me/api-keys")
    async def save_api_key(
        use_case: SaveApiKeyUseCase = Depends(get_save_api_key_use_case),
    ):
        return await use_case.execute(...)
"""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.composition.infrastructure import get_ai_service, get_database_session
from src.app.composition.repositories import get_user_repository
from src.app.config.app_config import AppConfig
from src.app.features.ai_config.application.services.refinement_provider_resolver import RefinementProviderResolver
from src.app.features.ai_config.application.use_cases.delete_api_key import DeleteApiKeyUseCase
from src.app.features.ai_config.application.use_cases.get_credit_balance import GetCreditBalanceUseCase
from src.app.features.ai_config.application.use_cases.list_api_keys import ListApiKeysUseCase
from src.app.features.ai_config.application.use_cases.save_api_key import SaveApiKeyUseCase
from src.app.features.ai_config.application.use_cases.validate_api_key import ValidateApiKeyUseCase
from src.app.features.ai_config.domain.repositories.user_api_key_repository import UserApiKeyRepository
from src.app.features.ai_config.domain.services.key_validation_throttle import KeyValidationThrottle
from src.app.features.ai_config.infrastructure.ai.provider_key_validator import ProviderKeyValidator
from src.app.features.ai_config.infrastructure.repositories.in_memory_key_validation_attempt_repository import (
    InMemoryKeyValidationAttemptRepository,
)
from src.app.features.ai_config.infrastructure.repositories.sql_key_validation_attempt_repository import (
    SqlKeyValidationAttemptRepository,
)
from src.app.features.ai_config.infrastructure.repositories.user_api_key_repository_impl import UserApiKeyRepositoryImpl
from src.app.features.refinement.infrastructure.ai.ai_service import AIService
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.infrastructure.security.api_key_cipher import ApiKeyCipher


@lru_cache(maxsize=1)
def get_api_key_cipher() -> ApiKeyCipher:
    """
    Cached singleton factory for ApiKeyCipher.

    Built once from `security.api_key_encryption_key`. Construction validates the key, so a
    misconfigured deployment surfaces on the first key operation rather than corrupting rows.
    """
    return ApiKeyCipher(AppConfig.instance().get_config("security.api_key_encryption_key", ""))


@lru_cache(maxsize=1)
def get_provider_key_validator() -> ProviderKeyValidator:
    """Cached singleton factory for ProviderKeyValidator (stateless, holds only a timeout)."""
    return ProviderKeyValidator()


# Process-local fallback for the validation budget, used only by the test profile. Shared at
# module level because the budget must survive across requests to mean anything.
_in_memory_validation_attempts = InMemoryKeyValidationAttemptRepository()


def _persist_validation_attempts() -> bool:
    """
    Whether the validation budget should be backed by Postgres.

    Mirrors `auth.persist_session_state`: true everywhere except the `test` profile, where
    presentation tests mock repositories and should not need a live database to charge a
    throttle that is incidental to what they assert.
    """
    return bool(AppConfig.instance().get_config("auth.persist_session_state", True))


async def get_user_api_key_repository(
    session: AsyncSession = Depends(get_database_session),
) -> UserApiKeyRepository:
    """User API key repository factory (feature-specific)."""
    return UserApiKeyRepositoryImpl(session)


async def get_key_validation_throttle(
    session: AsyncSession = Depends(get_database_session),
) -> KeyValidationThrottle:
    """KeyValidationThrottle factory, SQL-backed outside the test profile."""
    repository = (
        SqlKeyValidationAttemptRepository(session) if _persist_validation_attempts() else _in_memory_validation_attempts
    )
    return KeyValidationThrottle(repository)


async def get_refinement_provider_resolver(
    repository: UserApiKeyRepository = Depends(get_user_api_key_repository),
    platform_service: AIService = Depends(get_ai_service),
) -> RefinementProviderResolver:
    """
    RefinementProviderResolver factory.

    Bridges this feature into refinement: it decides whether a run uses the platform's
    singleton client (spending a credit) or a client built from the user's own key.
    """
    return RefinementProviderResolver(repository, get_api_key_cipher(), platform_service)


async def get_credit_balance_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> GetCreditBalanceUseCase:
    """GetCreditBalanceUseCase factory."""
    return GetCreditBalanceUseCase(user_repository)


async def get_list_api_keys_use_case(
    repository: UserApiKeyRepository = Depends(get_user_api_key_repository),
) -> ListApiKeysUseCase:
    """ListApiKeysUseCase factory."""
    return ListApiKeysUseCase(repository)


async def get_save_api_key_use_case(
    repository: UserApiKeyRepository = Depends(get_user_api_key_repository),
    throttle: KeyValidationThrottle = Depends(get_key_validation_throttle),
) -> SaveApiKeyUseCase:
    """SaveApiKeyUseCase factory."""
    return SaveApiKeyUseCase(repository, get_api_key_cipher(), get_provider_key_validator(), throttle)


async def get_delete_api_key_use_case(
    repository: UserApiKeyRepository = Depends(get_user_api_key_repository),
) -> DeleteApiKeyUseCase:
    """DeleteApiKeyUseCase factory."""
    return DeleteApiKeyUseCase(repository)


async def get_validate_api_key_use_case(
    repository: UserApiKeyRepository = Depends(get_user_api_key_repository),
    throttle: KeyValidationThrottle = Depends(get_key_validation_throttle),
) -> ValidateApiKeyUseCase:
    """ValidateApiKeyUseCase factory."""
    return ValidateApiKeyUseCase(repository, get_api_key_cipher(), get_provider_key_validator(), throttle)
