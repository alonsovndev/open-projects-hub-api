"""Re-test a stored provider API key."""

from src.app.features.ai_config.application.dtos.ai_config_dto import ValidateApiKeyResponse
from src.app.features.ai_config.domain.exceptions.ai_config_exceptions import ApiKeyNotFoundError, ApiKeyRejectedError
from src.app.features.ai_config.domain.repositories.user_api_key_repository import UserApiKeyRepository
from src.app.features.ai_config.domain.services.key_validation_throttle import KeyValidationThrottle
from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider
from src.app.features.ai_config.domain.value_objects.provider_failure_reason import ProviderFailureReason
from src.app.features.ai_config.infrastructure.ai.provider_key_validator import ProviderKeyValidator
from src.app.features.ai_config.infrastructure.crypto.key_decryption import decrypt_user_key
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.security.api_key_cipher import ApiKeyCipher
from src.app.shared.logging import get_logger, set_user_id


class ValidateApiKeyUseCase:
    """
    Checks a stored key still works, on demand (FR-010-05).

    Charged against the same per-user budget as saving, since it makes the same outbound
    call — otherwise this endpoint would be the unmetered way to probe provider APIs.
    """

    def __init__(
        self,
        repository: UserApiKeyRepository,
        cipher: ApiKeyCipher,
        validator: ProviderKeyValidator,
        throttle: KeyValidationThrottle,
    ):
        """
        Args:
            repository: Storage for user provider keys.
            cipher: AES-256-GCM decryption for the stored key material.
            validator: Live provider check.
            throttle: Per-user budget for validation attempts.
        """
        self._repository = repository
        self._cipher = cipher
        self._validator = validator
        self._throttle = throttle

    async def execute(self, provider: AIProvider, user_id: str) -> ValidateApiKeyResponse:
        """
        Test the caller's stored key for a provider.

        Args:
            provider: The provider whose key should be tested.
            user_id: The authenticated user's UUID string.

        Returns:
            ValidateApiKeyResponse reporting acceptance and any low-quota warning.

        Raises:
            ApiKeyNotFoundError: If the user has no key for that provider.
            KeyValidationRateLimitedError: If the user's validation budget is spent.
            ApiKeyRejectedError: If the provider refuses the key.
        """
        log = get_logger(__name__)
        set_user_id(user_id)

        stored = await self._repository.find_by_user_and_provider(EntityId.from_string(user_id), provider)
        if stored is None:
            raise ApiKeyNotFoundError(provider)

        # Decrypt before charging: the budget exists to meter outbound provider calls, and
        # a decryption failure (rotated master key, tampered row) never reaches one. Making
        # the user forfeit an attempt over it would penalize them for our problem.
        raw_key = await decrypt_user_key(self._cipher, stored, user_id)

        await self._throttle.consume(user_id)
        result = await self._validator.validate(raw_key, provider)

        if not result.valid:
            log.warning(
                "Provider refused a stored API key",
                extra={
                    "event_type": "ai_config.key.validation_failed",
                    "provider": provider.value,
                    "reason": (result.reason or ProviderFailureReason.NETWORK).value,
                },
            )
            raise ApiKeyRejectedError(
                provider=provider,
                reason=result.reason or ProviderFailureReason.NETWORK,
                retry_after=result.retry_after,
            )

        return ValidateApiKeyResponse(provider=provider, valid=True, quota_warning=result.quota_warning)
