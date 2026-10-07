"""Tests for RefinementProviderResolver (FR-010-03/06/08/09)."""

import base64
import logging
import os
from unittest.mock import AsyncMock

import pytest

from src.app.features.ai_config.application.services.refinement_provider_resolver import RefinementProviderResolver
from src.app.features.ai_config.domain.entities.user_api_key_entity import UserApiKeyEntity
from src.app.features.ai_config.domain.exceptions.ai_config_exceptions import ApiKeyNotFoundError
from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider, RefinementProvider
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.exceptions.user_exceptions import AICreditsExhaustedError
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.infrastructure.security.api_key_cipher import ApiKeyCipher


RAW_KEY = "sk-proj-abcdefghijklmnopqrstuv1234"


def build_admin(credits: int = 5) -> UserEntity:
    user = UserEntity.create(
        email="admin@example.com",
        display_name="Admin",
        password_hash="hashed",
        role=UserRole.ADMIN,
    )
    user._ai_credits_remaining = credits
    return user


def build_cipher() -> ApiKeyCipher:
    return ApiKeyCipher(base64.b64encode(os.urandom(32)).decode())


async def store_key(cipher: ApiKeyCipher, user: UserEntity, provider: AIProvider) -> UserApiKeyEntity:
    encrypted = await cipher.encrypt(RAW_KEY, str(user.id.value))
    return UserApiKeyEntity.create(
        user_id=user.id,
        provider=provider,
        ciphertext=encrypted.ciphertext,
        nonce=encrypted.nonce,
        key_version=encrypted.key_version,
        raw_key=RAW_KEY,
    )


class TestPlatformSelection:
    """Platform runs are gated on the credit balance before anything is called."""

    @pytest.mark.asyncio
    async def test_uses_the_platform_service_and_flags_a_credit(self):
        platform = AsyncMock()
        resolver = RefinementProviderResolver(AsyncMock(), build_cipher(), platform)

        resolved = await resolver.resolve(build_admin(credits=2), RefinementProvider.PLATFORM)

        assert resolved.service is platform
        assert resolved.consumes_credit is True

    @pytest.mark.asyncio
    async def test_refuses_a_platform_run_with_no_credits(self):
        """FR-010-03: an exhausted balance blocks before any provider is contacted."""
        resolver = RefinementProviderResolver(AsyncMock(), build_cipher(), AsyncMock())

        with pytest.raises(AICreditsExhaustedError, match="Add your own API key"):
            await resolver.resolve(build_admin(credits=0), RefinementProvider.PLATFORM)


class TestUserKeySelection:
    """A user-key run builds a fresh client and spends no platform credit."""

    @pytest.mark.asyncio
    async def test_builds_a_client_from_the_stored_key(self):
        user = build_admin(credits=5)
        cipher = build_cipher()
        repository = AsyncMock()
        repository.find_by_user_and_provider.return_value = await store_key(cipher, user, AIProvider.OPENAI)

        resolved = await RefinementProviderResolver(repository, cipher, AsyncMock()).resolve(
            user, RefinementProvider.OPENAI
        )

        assert resolved.consumes_credit is False
        assert resolved.service.provider_name == "openai"

    @pytest.mark.asyncio
    async def test_a_user_key_run_works_even_with_no_credits_left(self):
        """FR-010-08: the user's own quota is independent of the platform balance."""
        user = build_admin(credits=0)
        cipher = build_cipher()
        repository = AsyncMock()
        repository.find_by_user_and_provider.return_value = await store_key(cipher, user, AIProvider.GEMINI)

        resolved = await RefinementProviderResolver(repository, cipher, AsyncMock()).resolve(
            user, RefinementProvider.GEMINI
        )

        assert resolved.consumes_credit is False

    @pytest.mark.asyncio
    async def test_refuses_a_provider_the_user_has_no_key_for(self):
        repository = AsyncMock()
        repository.find_by_user_and_provider.return_value = None

        with pytest.raises(ApiKeyNotFoundError):
            await RefinementProviderResolver(repository, build_cipher(), AsyncMock()).resolve(
                build_admin(), RefinementProvider.DEEPSEEK
            )

    @pytest.mark.asyncio
    async def test_does_not_silently_fall_back_to_another_provider(self):
        """
        F-010 rules out automatic fallback: a missing key is an error the user resolves,
        not a licence to spend a different provider's quota on their behalf.
        """
        user = build_admin(credits=5)
        cipher = build_cipher()
        repository = AsyncMock()
        # The user holds a Gemini key, but asked for OpenAI.
        repository.find_by_user_and_provider.return_value = None
        platform = AsyncMock()

        with pytest.raises(ApiKeyNotFoundError):
            await RefinementProviderResolver(repository, cipher, platform).resolve(user, RefinementProvider.OPENAI)

        platform.generate_stories_from_notes.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_resolution_does_not_log_the_decrypted_key(self, caplog):
        """NFR-010-02: decryption happens here, so this is where a leak would surface."""
        user = build_admin(credits=5)
        cipher = build_cipher()
        repository = AsyncMock()
        repository.find_by_user_and_provider.return_value = await store_key(cipher, user, AIProvider.OPENAI)

        with caplog.at_level(logging.DEBUG):
            await RefinementProviderResolver(repository, cipher, AsyncMock()).resolve(user, RefinementProvider.OPENAI)

        assert RAW_KEY not in caplog.text


class TestDeletedKeyFallback:
    """FR-010-09 falls out of the same rule rather than being special-cased."""

    @pytest.mark.asyncio
    async def test_platform_still_serves_after_a_key_is_deleted_when_credits_remain(self):
        platform = AsyncMock()
        repository = AsyncMock()
        repository.find_by_user_and_provider.return_value = None

        resolved = await RefinementProviderResolver(repository, build_cipher(), platform).resolve(
            build_admin(credits=3), RefinementProvider.PLATFORM
        )

        assert resolved.service is platform

    @pytest.mark.asyncio
    async def test_refinement_is_blocked_after_a_key_is_deleted_with_no_credits(self):
        repository = AsyncMock()
        repository.find_by_user_and_provider.return_value = None

        with pytest.raises(AICreditsExhaustedError):
            await RefinementProviderResolver(repository, build_cipher(), AsyncMock()).resolve(
                build_admin(credits=0), RefinementProvider.PLATFORM
            )
