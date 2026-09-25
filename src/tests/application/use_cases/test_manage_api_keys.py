"""Tests for the API key management use cases (FR-010-04/05/07/09, NFR-010-01/03)."""

import base64
import logging
import os
from unittest.mock import AsyncMock

import pytest

from src.app.features.ai_config.application.dtos.ai_config_dto import SaveApiKeyRequest
from src.app.features.ai_config.application.use_cases.delete_api_key import DeleteApiKeyUseCase
from src.app.features.ai_config.application.use_cases.list_api_keys import ListApiKeysUseCase
from src.app.features.ai_config.application.use_cases.save_api_key import SaveApiKeyUseCase
from src.app.features.ai_config.application.use_cases.validate_api_key import ValidateApiKeyUseCase
from src.app.features.ai_config.domain.entities.user_api_key_entity import UserApiKeyEntity
from src.app.features.ai_config.domain.exceptions.ai_config_exceptions import (
    ApiKeyNotFoundError,
    ApiKeyRejectedError,
    KeyValidationRateLimitedError,
)
from src.app.features.ai_config.domain.services.key_validation_throttle import KeyValidationThrottle
from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider
from src.app.features.ai_config.domain.value_objects.provider_failure_reason import ProviderFailureReason
from src.app.features.ai_config.infrastructure.ai.provider_key_validator import KeyValidationResult
from src.app.features.ai_config.infrastructure.repositories.in_memory_key_validation_attempt_repository import (
    InMemoryKeyValidationAttemptRepository,
)
from src.app.shared.domain.exceptions.domain_exceptions import ValidationError
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.security.api_key_cipher import ApiKeyCipher, ApiKeyDecryptionError, EncryptedApiKey


RAW_KEY = "sk-proj-abcdefghijklmnopqrstuv1234"
REPLACEMENT_KEY = "sk-proj-zyxwvutsrqponmlkjihgf9876"
USER_ID = "8f14e45f-ceea-467a-9f84-9e0b1c2d3e4f"


def build_cipher() -> ApiKeyCipher:
    return ApiKeyCipher(base64.b64encode(os.urandom(32)).decode())


def as_encrypted(entity: UserApiKeyEntity) -> EncryptedApiKey:
    """Reassemble a stored entity into the payload the cipher can open."""
    return EncryptedApiKey(
        ciphertext=entity.ciphertext,
        nonce=entity.nonce,
        key_version=entity.key_version,
    )


def accepting_validator(quota_ratio: float | None = None) -> AsyncMock:
    validator = AsyncMock()
    validator.validate.return_value = KeyValidationResult(valid=True, quota_consumed_ratio=quota_ratio)
    return validator


def refusing_validator(reason: ProviderFailureReason, retry_after: str | None = None) -> AsyncMock:
    validator = AsyncMock()
    validator.validate.return_value = KeyValidationResult(valid=False, reason=reason, retry_after=retry_after)
    return validator


def build_throttle() -> KeyValidationThrottle:
    return KeyValidationThrottle(InMemoryKeyValidationAttemptRepository())


class TestSaveApiKey:
    """Saving validates, encrypts, and rotates in place."""

    @pytest.mark.asyncio
    async def test_stores_an_encrypted_key_and_returns_only_the_mask(self):
        repository = AsyncMock()
        repository.find_by_user_and_provider.return_value = None
        repository.upsert.side_effect = lambda entity: entity
        cipher = build_cipher()

        use_case = SaveApiKeyUseCase(repository, cipher, accepting_validator(), build_throttle())
        response = await use_case.execute(
            SaveApiKeyRequest(provider=AIProvider.OPENAI, api_key=RAW_KEY), user_id=USER_ID
        )

        stored = repository.upsert.await_args.args[0]
        assert RAW_KEY.encode() not in stored.ciphertext
        assert await cipher.decrypt(as_encrypted(stored), USER_ID) == RAW_KEY
        assert response.masked_key == "sk-proj***...1234"
        assert RAW_KEY not in response.model_dump_json()

    @pytest.mark.asyncio
    async def test_rejects_a_malformed_key_without_calling_the_provider(self):
        """An obvious typo must not cost a validation attempt or an outbound call."""
        validator = accepting_validator()
        throttle = build_throttle()
        use_case = SaveApiKeyUseCase(AsyncMock(), build_cipher(), validator, throttle)

        with pytest.raises(ValidationError):
            await use_case.execute(
                SaveApiKeyRequest(provider=AIProvider.OPENAI, api_key="AIza-wrong-provider-prefix"),
                user_id=USER_ID,
            )

        validator.validate.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_a_refused_key_is_not_stored(self):
        repository = AsyncMock()
        use_case = SaveApiKeyUseCase(
            repository,
            build_cipher(),
            refusing_validator(ProviderFailureReason.AUTH_FAILED),
            build_throttle(),
        )

        with pytest.raises(ApiKeyRejectedError) as exc_info:
            await use_case.execute(SaveApiKeyRequest(provider=AIProvider.OPENAI, api_key=RAW_KEY), user_id=USER_ID)

        assert exc_info.value.reason is ProviderFailureReason.AUTH_FAILED
        repository.upsert.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_saving_again_rotates_the_secret_in_place(self):
        """US-EP6-BE-003: the previous ciphertext is overwritten, leaving no usable copy."""
        cipher = build_cipher()
        encrypted = await cipher.encrypt(RAW_KEY, USER_ID)
        existing = UserApiKeyEntity.create(
            user_id=EntityId.from_string(USER_ID),
            provider=AIProvider.OPENAI,
            ciphertext=encrypted.ciphertext,
            nonce=encrypted.nonce,
            key_version=encrypted.key_version,
            raw_key=RAW_KEY,
        )
        original_ciphertext = existing.ciphertext

        repository = AsyncMock()
        repository.find_by_user_and_provider.return_value = existing
        repository.upsert.side_effect = lambda entity: entity

        use_case = SaveApiKeyUseCase(repository, cipher, accepting_validator(), build_throttle())
        await use_case.execute(SaveApiKeyRequest(provider=AIProvider.OPENAI, api_key=REPLACEMENT_KEY), user_id=USER_ID)

        rotated = repository.upsert.await_args.args[0]
        assert rotated.ciphertext != original_ciphertext
        assert await cipher.decrypt(as_encrypted(rotated), USER_ID) == REPLACEMENT_KEY
        assert rotated.masked_key == "sk-proj***...9876"

    @pytest.mark.asyncio
    async def test_the_sixth_save_in_an_hour_is_rate_limited(self):
        repository = AsyncMock()
        repository.find_by_user_and_provider.return_value = None
        repository.upsert.side_effect = lambda entity: entity
        throttle = build_throttle()
        use_case = SaveApiKeyUseCase(repository, build_cipher(), accepting_validator(), throttle)

        request = SaveApiKeyRequest(provider=AIProvider.OPENAI, api_key=RAW_KEY)
        for _ in range(KeyValidationThrottle.MAX_ATTEMPTS):
            await use_case.execute(request, user_id=USER_ID)

        with pytest.raises(KeyValidationRateLimitedError):
            await use_case.execute(request, user_id=USER_ID)

    @pytest.mark.asyncio
    async def test_no_log_record_contains_the_raw_key(self, caplog):
        """NFR-010-02: the key must not reach any log line on the save path."""
        repository = AsyncMock()
        repository.find_by_user_and_provider.return_value = None
        repository.upsert.side_effect = lambda entity: entity
        use_case = SaveApiKeyUseCase(repository, build_cipher(), accepting_validator(), build_throttle())

        with caplog.at_level(logging.DEBUG):
            await use_case.execute(SaveApiKeyRequest(provider=AIProvider.OPENAI, api_key=RAW_KEY), user_id=USER_ID)

        assert RAW_KEY not in caplog.text
        assert "abcdefghijklmnopqrstuv" not in caplog.text

    @pytest.mark.asyncio
    async def test_a_rejection_does_not_log_the_raw_key(self, caplog):
        use_case = SaveApiKeyUseCase(
            AsyncMock(),
            build_cipher(),
            refusing_validator(ProviderFailureReason.AUTH_FAILED),
            build_throttle(),
        )

        with caplog.at_level(logging.DEBUG), pytest.raises(ApiKeyRejectedError) as exc_info:
            await use_case.execute(SaveApiKeyRequest(provider=AIProvider.OPENAI, api_key=RAW_KEY), user_id=USER_ID)

        assert RAW_KEY not in caplog.text
        assert RAW_KEY not in str(exc_info.value)


class TestListApiKeys:
    """Listing exposes masks only — there is no plaintext read path (FR-010-07)."""

    @pytest.mark.asyncio
    async def test_returns_masked_entries_only(self):
        cipher = build_cipher()
        encrypted = await cipher.encrypt(RAW_KEY, USER_ID)
        repository = AsyncMock()
        repository.find_by_user.return_value = [
            UserApiKeyEntity.create(
                user_id=EntityId.from_string(USER_ID),
                provider=AIProvider.OPENAI,
                ciphertext=encrypted.ciphertext,
                nonce=encrypted.nonce,
                key_version=encrypted.key_version,
                raw_key=RAW_KEY,
            )
        ]

        response = await ListApiKeysUseCase(repository).execute(user_id=USER_ID)

        assert len(response.keys) == 1
        assert response.keys[0].masked_key == "sk-proj***...1234"
        assert RAW_KEY not in response.model_dump_json()


class TestDeleteApiKey:
    """Deletion is a hard delete and reports a missing key honestly (NFR-010-04)."""

    @pytest.mark.asyncio
    async def test_deletes_the_key(self):
        repository = AsyncMock()
        repository.delete.return_value = True

        await DeleteApiKeyUseCase(repository).execute(provider=AIProvider.OPENAI, user_id=USER_ID)

        repository.delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_when_there_is_nothing_to_delete(self):
        repository = AsyncMock()
        repository.delete.return_value = False

        with pytest.raises(ApiKeyNotFoundError):
            await DeleteApiKeyUseCase(repository).execute(provider=AIProvider.GEMINI, user_id=USER_ID)


class TestValidateApiKey:
    """Re-testing a stored key is charged against the same budget as saving one."""

    @staticmethod
    async def _stored_key(cipher: ApiKeyCipher) -> UserApiKeyEntity:
        encrypted = await cipher.encrypt(RAW_KEY, USER_ID)
        return UserApiKeyEntity.create(
            user_id=EntityId.from_string(USER_ID),
            provider=AIProvider.OPENAI,
            ciphertext=encrypted.ciphertext,
            nonce=encrypted.nonce,
            key_version=encrypted.key_version,
            raw_key=RAW_KEY,
        )

    @pytest.mark.asyncio
    async def test_reports_a_working_key(self):
        cipher = build_cipher()
        repository = AsyncMock()
        repository.find_by_user_and_provider.return_value = await self._stored_key(cipher)

        response = await ValidateApiKeyUseCase(repository, cipher, accepting_validator(), build_throttle()).execute(
            provider=AIProvider.OPENAI, user_id=USER_ID
        )

        assert response.valid is True
        assert response.quota_warning is False

    @pytest.mark.asyncio
    async def test_warns_when_provider_quota_passes_eighty_percent(self):
        """FR-010-12: surface the low-quota banner when the provider reports usage."""
        cipher = build_cipher()
        repository = AsyncMock()
        repository.find_by_user_and_provider.return_value = await self._stored_key(cipher)

        response = await ValidateApiKeyUseCase(
            repository, cipher, accepting_validator(quota_ratio=0.85), build_throttle()
        ).execute(provider=AIProvider.OPENAI, user_id=USER_ID)

        assert response.quota_warning is True

    @pytest.mark.asyncio
    async def test_does_not_warn_below_the_threshold(self):
        cipher = build_cipher()
        repository = AsyncMock()
        repository.find_by_user_and_provider.return_value = await self._stored_key(cipher)

        response = await ValidateApiKeyUseCase(
            repository, cipher, accepting_validator(quota_ratio=0.5), build_throttle()
        ).execute(provider=AIProvider.OPENAI, user_id=USER_ID)

        assert response.quota_warning is False

    @pytest.mark.asyncio
    async def test_raises_when_no_key_is_configured(self):
        repository = AsyncMock()
        repository.find_by_user_and_provider.return_value = None

        with pytest.raises(ApiKeyNotFoundError):
            await ValidateApiKeyUseCase(repository, build_cipher(), accepting_validator(), build_throttle()).execute(
                provider=AIProvider.DEEPSEEK, user_id=USER_ID
            )

    @pytest.mark.asyncio
    async def test_a_now_invalid_key_reports_the_reason(self):
        """FR-010-11: an expired key surfaces as a key problem, not a generic outage."""
        cipher = build_cipher()
        repository = AsyncMock()
        repository.find_by_user_and_provider.return_value = await self._stored_key(cipher)

        with pytest.raises(ApiKeyRejectedError) as exc_info:
            await ValidateApiKeyUseCase(
                repository, cipher, refusing_validator(ProviderFailureReason.AUTH_FAILED), build_throttle()
            ).execute(provider=AIProvider.OPENAI, user_id=USER_ID)

        assert exc_info.value.reason.prompts_key_update is True

    @pytest.mark.asyncio
    async def test_validation_does_not_log_the_decrypted_key(self, caplog):
        cipher = build_cipher()
        repository = AsyncMock()
        repository.find_by_user_and_provider.return_value = await self._stored_key(cipher)

        with caplog.at_level(logging.DEBUG):
            await ValidateApiKeyUseCase(repository, cipher, accepting_validator(), build_throttle()).execute(
                provider=AIProvider.OPENAI, user_id=USER_ID
            )

        assert RAW_KEY not in caplog.text


class TestValidationBudgetOrdering:
    """The budget meters outbound provider calls, so nothing that fails earlier spends it."""

    @pytest.mark.asyncio
    async def test_an_undecryptable_key_does_not_cost_an_attempt(self):
        """A rotated master key is our failure, not the user's — it must not burn a try."""
        user_key = await TestValidateApiKey._stored_key(build_cipher())
        repository = AsyncMock()
        repository.find_by_user_and_provider.return_value = user_key
        throttle = build_throttle()

        # A different cipher stands in for a master key that has since been rotated.
        use_case = ValidateApiKeyUseCase(repository, build_cipher(), accepting_validator(), throttle)

        with pytest.raises(ApiKeyDecryptionError):
            await use_case.execute(provider=AIProvider.OPENAI, user_id=USER_ID)

        # The full budget is still available.
        for _ in range(KeyValidationThrottle.MAX_ATTEMPTS):
            await throttle.consume(USER_ID)

    @pytest.mark.asyncio
    async def test_a_missing_key_does_not_cost_an_attempt(self):
        repository = AsyncMock()
        repository.find_by_user_and_provider.return_value = None
        throttle = build_throttle()

        with pytest.raises(ApiKeyNotFoundError):
            await ValidateApiKeyUseCase(repository, build_cipher(), accepting_validator(), throttle).execute(
                provider=AIProvider.OPENAI, user_id=USER_ID
            )

        for _ in range(KeyValidationThrottle.MAX_ATTEMPTS):
            await throttle.consume(USER_ID)
