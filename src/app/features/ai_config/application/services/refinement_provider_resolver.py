"""Decides which AI provider serves a refinement, and who pays for it."""

from dataclasses import dataclass

from src.app.features.ai_config.domain.exceptions.ai_config_exceptions import ApiKeyNotFoundError
from src.app.features.ai_config.domain.repositories.user_api_key_repository import UserApiKeyRepository
from src.app.features.ai_config.domain.value_objects.ai_provider import RefinementProvider
from src.app.features.ai_config.infrastructure.ai.user_ai_service_factory import create_user_ai_service
from src.app.features.ai_config.infrastructure.crypto.key_decryption import decrypt_user_key
from src.app.features.refinement.infrastructure.ai.ai_service import AIService
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.exceptions.user_exceptions import AICreditsExhaustedError
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.security.api_key_cipher import ApiKeyCipher


@dataclass(frozen=True)
class ResolvedProvider:
    """The client to run a refinement through, and whether it costs a platform credit."""

    service: AIService
    consumes_credit: bool


class RefinementProviderResolver:
    """
    Turns a requested provider into a ready-to-use AI client.

    This is the single seam between AI monetization and the refinement workflow. Selection
    is explicit: the user picks a provider per run and we honour it or fail. There is no
    silent fallback to another provider — F-010 rules that out, and quietly spending a
    different key's quota is not a decision to make on the user's behalf.

    Deleting a key is handled by the same rule rather than by special-casing deletion: a
    user who removes their key simply asks for `PLATFORM` next time, which succeeds while
    credits remain and raises `AICreditsExhaustedError` once they do not (FR-010-09).
    """

    def __init__(
        self,
        repository: UserApiKeyRepository,
        cipher: ApiKeyCipher,
        platform_service: AIService,
    ):
        """
        Args:
            repository: Storage for user provider keys.
            cipher: AES-256-GCM decryption for stored key material.
            platform_service: The application-wide client used for free credits.
        """
        self._repository = repository
        self._cipher = cipher
        self._platform_service = platform_service

    async def resolve(self, user: UserEntity, requested: RefinementProvider) -> ResolvedProvider:
        """
        Pick the client for one refinement run.

        Args:
            user: The user requesting the refinement, carrying their credit balance.
            requested: The provider the user selected.

        Returns:
            ResolvedProvider with the client and whether a credit will be spent.

        Raises:
            AICreditsExhaustedError: If PLATFORM was requested with no credits left.
            ApiKeyNotFoundError: If a user provider was requested without a stored key.
        """
        if requested.is_platform:
            if not user.has_ai_credits():
                raise AICreditsExhaustedError
            return ResolvedProvider(service=self._platform_service, consumes_credit=True)

        provider = requested.to_api_provider()
        user_id = str(user.id.value)

        stored = await self._repository.find_by_user_and_provider(EntityId(user.id.value), provider)
        if stored is None:
            raise ApiKeyNotFoundError(provider)

        raw_key = await decrypt_user_key(self._cipher, stored, user_id)

        # Built per request and never cached: this client holds one user's decrypted key.
        return ResolvedProvider(
            service=create_user_ai_service(provider, raw_key),
            consumes_credit=False,
        )
