"""Authenticated encryption for user-supplied AI provider API keys (F-010 NFR-010-01)."""

import asyncio
import base64
import binascii
import os
from dataclasses import dataclass

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionKeyError(Exception):
    """Raised when the configured master encryption key is missing or unusable."""


class ApiKeyDecryptionError(Exception):
    """
    Raised when stored ciphertext cannot be decrypted.

    Carries no detail about the ciphertext or the key: this reaches an HTTP error path,
    and the whole point of the class is that key material never escapes.
    """


# AES-256-GCM. 32-byte key, 12-byte nonce (the size GCM is specified for).
_KEY_BYTES = 32
_NONCE_BYTES = 12

# Stamped on every ciphertext so a future re-encryption can tell which master key
# produced a row. Bump alongside the rotation runbook in ADR-018.
CURRENT_KEY_VERSION = 1

# Placeholder values that reach us from an unset `!ENV ${API_KEY_ENCRYPTION_KEY}`
# (pyaml_env substitutes "N/A") or a half-filled .env.
_PLACEHOLDER_KEYS = {"", "n/a", "none", "null", "changeme"}


@dataclass(frozen=True)
class EncryptedApiKey:
    """Ciphertext plus everything needed to decrypt it later."""

    ciphertext: bytes
    nonce: bytes
    key_version: int


class ApiKeyCipher:
    """
    Encrypts and decrypts provider API keys with AES-256-GCM.

    Instantiated once at the composition root from the base64 master key in config.
    Encryption is offloaded with `asyncio.to_thread` to match `PasswordHandler`, keeping
    the event loop free even though AES-GCM on a short string is cheap.

    The `user_id` passed to `encrypt`/`decrypt` is bound as GCM associated data, so a
    ciphertext copied onto another user's row fails authentication instead of decrypting.
    """

    def __init__(self, master_key_b64: str):
        """
        Args:
            master_key_b64: Base64-encoded 32-byte master key.

        Raises:
            EncryptionKeyError: If the key is absent, a placeholder, not valid base64,
                or not exactly 32 bytes.
        """
        if not master_key_b64 or master_key_b64.strip().lower() in _PLACEHOLDER_KEYS:
            raise EncryptionKeyError(
                "API_KEY_ENCRYPTION_KEY is not configured. Generate one with: "
                'python -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode())"'
            )

        try:
            master_key = base64.b64decode(master_key_b64.strip(), validate=True)
        except (binascii.Error, ValueError) as e:
            raise EncryptionKeyError("API_KEY_ENCRYPTION_KEY must be valid base64") from e

        if len(master_key) != _KEY_BYTES:
            raise EncryptionKeyError(
                f"API_KEY_ENCRYPTION_KEY must decode to {_KEY_BYTES} bytes for AES-256, got {len(master_key)}"
            )

        self._aesgcm = AESGCM(master_key)

    async def encrypt(self, plaintext: str, user_id: str) -> EncryptedApiKey:
        """
        Encrypt a provider API key.

        Args:
            plaintext: The raw provider API key.
            user_id: Owner's UUID string, bound as associated data.

        Returns:
            EncryptedApiKey carrying the ciphertext, its nonce, and the key version.
        """
        nonce = os.urandom(_NONCE_BYTES)

        def _encrypt() -> bytes:
            return self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), user_id.encode("utf-8"))

        ciphertext = await asyncio.to_thread(_encrypt)
        return EncryptedApiKey(ciphertext=ciphertext, nonce=nonce, key_version=CURRENT_KEY_VERSION)

    async def decrypt(self, encrypted: EncryptedApiKey, user_id: str) -> str:
        """
        Decrypt a stored provider API key.

        Args:
            encrypted: Stored ciphertext, nonce, and key version.
            user_id: Owner's UUID string, must match the value used to encrypt.

        Returns:
            The raw provider API key.

        Raises:
            ApiKeyDecryptionError: If the ciphertext fails authentication, which covers a
                wrong master key, a tampered row, and a row moved between users.
        """
        if encrypted.key_version != CURRENT_KEY_VERSION:
            raise ApiKeyDecryptionError(
                f"Stored key was encrypted with key version {encrypted.key_version}, "
                f"but this deployment holds version {CURRENT_KEY_VERSION}"
            )

        def _decrypt() -> bytes:
            return self._aesgcm.decrypt(encrypted.nonce, encrypted.ciphertext, user_id.encode("utf-8"))

        try:
            plaintext = await asyncio.to_thread(_decrypt)
        except InvalidTag as e:
            raise ApiKeyDecryptionError("Stored API key could not be decrypted") from e

        return plaintext.decode("utf-8")
