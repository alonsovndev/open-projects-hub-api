"""Bridge between a stored key entity and the cipher that can open it."""

from src.app.features.ai_config.domain.entities.user_api_key_entity import UserApiKeyEntity
from src.app.shared.infrastructure.security.api_key_cipher import ApiKeyCipher, EncryptedApiKey


async def decrypt_user_key(cipher: ApiKeyCipher, api_key: UserApiKeyEntity, user_id: str) -> str:
    """
    Recover the plaintext provider key from a stored record.

    The entity deliberately does not know about `EncryptedApiKey` — that would put an
    infrastructure type in the domain — so the reassembly lives here, where both the
    validation use case and the refinement resolver can share it.

    The returned plaintext must be passed straight to a provider client and never logged,
    stored, or placed in a response.

    Args:
        cipher: The configured AES-256-GCM cipher.
        api_key: The stored key record.
        user_id: The owner's UUID string, checked as GCM associated data.

    Returns:
        The raw provider API key.

    Raises:
        ApiKeyDecryptionError: If the ciphertext fails authentication.
    """
    return await cipher.decrypt(
        EncryptedApiKey(
            ciphertext=api_key.ciphertext,
            nonce=api_key.nonce,
            key_version=api_key.key_version,
        ),
        user_id,
    )
