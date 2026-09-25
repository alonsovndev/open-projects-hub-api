"""Add or replace a user's provider API key."""

from datetime import UTC, datetime

from src.app.features.ai_config.application.dtos.ai_config_dto import ApiKeyResponse, SaveApiKeyRequest
from src.app.features.ai_config.application.mappers.api_key_mapper import to_api_key_response
from src.app.features.ai_config.domain.entities.user_api_key_entity import UserApiKeyEntity
from src.app.features.ai_config.domain.exceptions.ai_config_exceptions import ApiKeyRejectedError
from src.app.features.ai_config.domain.repositories.user_api_key_repository import UserApiKeyRepository
from src.app.features.ai_config.domain.services.key_validation_throttle import KeyValidationThrottle
from src.app.features.ai_config.domain.validators.api_key_validators import ApiKeyValidators
from src.app.features.ai_config.domain.value_objects.provider_failure_reason import ProviderFailureReason
from src.app.features.ai_config.infrastructure.ai.provider_key_validator import ProviderKeyValidator
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.security.api_key_cipher import ApiKeyCipher
from src.app.shared.logging import get_logger, set_user_id


class SaveApiKeyUseCase:
    """
    Validates a provider key, then stores it encrypted (FR-010-04/05, NFR-010-01).

    Saving is also the rotation path: a second save for the same provider overwrites the
    stored ciphertext, so the previous key stops working immediately and leaves no
    recoverable copy behind (US-EP6-BE-003).
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
            cipher: AES-256-GCM encryption for the key material.
            validator: Live provider check performed before the key is accepted.
            throttle: Per-user budget for validation attempts.
        """
        self._repository = repository
        self._cipher = cipher
        self._validator = validator
        self._throttle = throttle

    async def execute(self, request: SaveApiKeyRequest, user_id: str) -> ApiKeyResponse:
        """
        Validate and store a provider key.

        Ordering matters: the local format check runs first so an obvious typo costs
        nothing, then the throttle is charged, and only then do we call the provider.

        Args:
            request: Provider and the raw key to store.
            user_id: The authenticated user's UUID string.

        Returns:
            ApiKeyResponse describing the stored key in masked form.

        Raises:
            ValidationError: If the key does not look like one this provider issues.
            KeyValidationRateLimitedError: If the user's validation budget is spent.
            ApiKeyRejectedError: If the provider refuses the key.
        """
        log = get_logger(__name__)
        set_user_id(user_id)

        raw_key = request.api_key.strip()
        provider = request.provider

        ApiKeyValidators.validate_format(raw_key, provider)

        await self._throttle.consume(user_id)

        result = await self._validator.validate(raw_key, provider)
        if not result.valid:
            log.warning(
                "Provider refused an API key on save",
                extra={
                    "event_type": "ai_config.key.rejected",
                    "provider": provider.value,
                    "reason": (result.reason or ProviderFailureReason.NETWORK).value,
                },
            )
            raise ApiKeyRejectedError(
                provider=provider,
                reason=result.reason or ProviderFailureReason.NETWORK,
                retry_after=result.retry_after,
            )

        owner_id = EntityId.from_string(user_id)
        encrypted = await self._cipher.encrypt(raw_key, user_id)
        validated_at = datetime.now(tz=UTC)

        existing = await self._repository.find_by_user_and_provider(owner_id, provider)

        if existing is None:
            api_key = UserApiKeyEntity.create(
                user_id=owner_id,
                provider=provider,
                ciphertext=encrypted.ciphertext,
                nonce=encrypted.nonce,
                key_version=encrypted.key_version,
                raw_key=raw_key,
                validated_at=validated_at,
            )
        else:
            existing.replace_secret(
                ciphertext=encrypted.ciphertext,
                nonce=encrypted.nonce,
                key_version=encrypted.key_version,
                raw_key=raw_key,
                validated_at=validated_at,
            )
            api_key = existing

        saved = await self._repository.upsert(api_key)

        log.info(
            "Provider API key stored",
            extra={
                "event_type": "ai_config.key.saved",
                "provider": provider.value,
                "rotated": existing is not None,
            },
        )

        return to_api_key_response(saved)
