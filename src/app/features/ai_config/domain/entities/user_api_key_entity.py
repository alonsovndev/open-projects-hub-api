"""User-owned AI provider API key."""

from datetime import UTC, datetime

from src.app.features.ai_config.domain.services.api_key_masker import ApiKeyMasker
from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider
from src.app.shared.domain.entities.base_entity import BaseEntity
from src.app.shared.domain.value_objects.entity_id import EntityId


class UserApiKeyEntity(BaseEntity):
    """
    One provider key belonging to one user.

    The entity never holds plaintext. It carries the ciphertext produced by `ApiKeyCipher`
    plus the mask shown in the UI, so no layer above infrastructure can accidentally read
    or log the key. Decryption happens only at the point of calling a provider.
    """

    def __init__(
        self,
        id: EntityId,
        user_id: EntityId,
        provider: AIProvider,
        ciphertext: bytes,
        nonce: bytes,
        key_version: int,
        masked_key: str,
        last_validated_at: datetime | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        """
        Args:
            id: Unique key identifier.
            user_id: Owning user.
            provider: Provider this key authenticates against.
            ciphertext: AES-256-GCM ciphertext of the raw key.
            nonce: Nonce used to produce `ciphertext`.
            key_version: Master-key version the ciphertext was produced under.
            masked_key: Display form, the only representation exposed by the API.
            last_validated_at: When the provider last accepted this key.
            created_at: Creation timestamp.
            updated_at: Last update timestamp.
        """
        now = datetime.now(UTC)
        super().__init__(id=id, created_at=created_at or now, updated_at=updated_at or now)

        self.user_id = user_id
        self.provider = provider
        self.ciphertext = ciphertext
        self.nonce = nonce
        self.key_version = key_version
        self.masked_key = masked_key
        self.last_validated_at = last_validated_at

    @classmethod
    def create(
        cls,
        user_id: EntityId,
        provider: AIProvider,
        ciphertext: bytes,
        nonce: bytes,
        key_version: int,
        raw_key: str,
        validated_at: datetime | None = None,
    ) -> "UserApiKeyEntity":
        """
        Build a new key record.

        `raw_key` is used only to compute the mask and is not retained on the entity.

        Args:
            user_id: Owning user.
            provider: Provider this key authenticates against.
            ciphertext: AES-256-GCM ciphertext of `raw_key`.
            nonce: Nonce used to produce `ciphertext`.
            key_version: Master-key version the ciphertext was produced under.
            raw_key: The plaintext key, read once to derive the display mask.
            validated_at: When the provider accepted this key, if it has been checked.

        Returns:
            A new UserApiKeyEntity.
        """
        return cls(
            id=EntityId.generate(),
            user_id=user_id,
            provider=provider,
            ciphertext=ciphertext,
            nonce=nonce,
            key_version=key_version,
            masked_key=ApiKeyMasker.mask(raw_key),
            last_validated_at=validated_at,
        )

    def replace_secret(
        self,
        ciphertext: bytes,
        nonce: bytes,
        key_version: int,
        raw_key: str,
        validated_at: datetime | None = None,
    ) -> None:
        """
        Rotate this record onto a new secret.

        The previous ciphertext is overwritten rather than kept alongside the new one, so
        the old key stops working the moment the row is saved (US-EP6-BE-003).

        Args:
            ciphertext: AES-256-GCM ciphertext of the replacement key.
            nonce: Nonce used to produce `ciphertext`.
            key_version: Master-key version the ciphertext was produced under.
            raw_key: The replacement plaintext, read once to derive the display mask.
            validated_at: When the provider accepted the replacement.
        """
        self.ciphertext = ciphertext
        self.nonce = nonce
        self.key_version = key_version
        self.masked_key = ApiKeyMasker.mask(raw_key)
        self.last_validated_at = validated_at
        self.mark_as_updated()

    def __repr__(self) -> str:
        """Masked representation, so an accidental log or traceback cannot leak the key."""
        return f"UserApiKeyEntity(provider={self.provider.value}, masked_key={self.masked_key})"
