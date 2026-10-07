"""Tests for ApiKeyCipher (F-010 NFR-010-01)."""

import base64
import os

import pytest

from src.app.shared.infrastructure.security.api_key_cipher import (
    ApiKeyCipher,
    ApiKeyDecryptionError,
    EncryptedApiKey,
    EncryptionKeyError,
)


RAW_KEY = "sk-proj-abcdefghijklmnopqrstuvwxyz0123"
USER_ID = "8f14e45f-ceea-467a-9f84-9e0b1c2d3e4f"
OTHER_USER_ID = "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d"


def make_cipher() -> ApiKeyCipher:
    return ApiKeyCipher(base64.b64encode(os.urandom(32)).decode())


class TestApiKeyCipherConstruction:
    """The master key is validated up front so misconfiguration cannot corrupt rows."""

    @pytest.mark.parametrize("key", ["", "   ", "N/A", "none", "changeme"])
    def test_rejects_missing_or_placeholder_keys(self, key):
        with pytest.raises(EncryptionKeyError):
            ApiKeyCipher(key)

    def test_rejects_non_base64(self):
        with pytest.raises(EncryptionKeyError, match="base64"):
            ApiKeyCipher("not!valid!base64!!!")

    def test_rejects_a_key_that_is_not_256_bits(self):
        with pytest.raises(EncryptionKeyError, match="32 bytes"):
            ApiKeyCipher(base64.b64encode(os.urandom(16)).decode())

    def test_accepts_a_32_byte_key(self):
        assert make_cipher() is not None


class TestApiKeyCipherRoundTrip:
    """Encryption must be reversible for the owner and useless to anyone else."""

    @pytest.mark.asyncio
    async def test_round_trip_recovers_the_key(self):
        cipher = make_cipher()
        encrypted = await cipher.encrypt(RAW_KEY, USER_ID)
        assert await cipher.decrypt(encrypted, USER_ID) == RAW_KEY

    @pytest.mark.asyncio
    async def test_ciphertext_does_not_contain_the_plaintext(self):
        cipher = make_cipher()
        encrypted = await cipher.encrypt(RAW_KEY, USER_ID)
        assert RAW_KEY.encode() not in encrypted.ciphertext
        assert b"sk-proj" not in encrypted.ciphertext

    @pytest.mark.asyncio
    async def test_the_same_key_encrypts_differently_each_time(self):
        """A fresh nonce per call stops identical keys producing identical rows."""
        cipher = make_cipher()
        first = await cipher.encrypt(RAW_KEY, USER_ID)
        second = await cipher.encrypt(RAW_KEY, USER_ID)
        assert first.ciphertext != second.ciphertext
        assert first.nonce != second.nonce

    @pytest.mark.asyncio
    async def test_a_ciphertext_moved_to_another_user_fails_to_decrypt(self):
        """The owner is bound as associated data, so a copied row is not usable."""
        cipher = make_cipher()
        encrypted = await cipher.encrypt(RAW_KEY, USER_ID)
        with pytest.raises(ApiKeyDecryptionError):
            await cipher.decrypt(encrypted, OTHER_USER_ID)

    @pytest.mark.asyncio
    async def test_a_tampered_ciphertext_is_rejected(self):
        cipher = make_cipher()
        encrypted = await cipher.encrypt(RAW_KEY, USER_ID)
        tampered = EncryptedApiKey(
            ciphertext=encrypted.ciphertext[:-1] + bytes([encrypted.ciphertext[-1] ^ 0x01]),
            nonce=encrypted.nonce,
            key_version=encrypted.key_version,
        )
        with pytest.raises(ApiKeyDecryptionError):
            await cipher.decrypt(tampered, USER_ID)

    @pytest.mark.asyncio
    async def test_a_different_master_key_cannot_decrypt(self):
        encrypted = await make_cipher().encrypt(RAW_KEY, USER_ID)
        with pytest.raises(ApiKeyDecryptionError):
            await make_cipher().decrypt(encrypted, USER_ID)

    @pytest.mark.asyncio
    async def test_an_unknown_key_version_is_refused_rather_than_guessed(self):
        cipher = make_cipher()
        encrypted = await cipher.encrypt(RAW_KEY, USER_ID)
        stale = EncryptedApiKey(
            ciphertext=encrypted.ciphertext,
            nonce=encrypted.nonce,
            key_version=encrypted.key_version + 1,
        )
        with pytest.raises(ApiKeyDecryptionError, match="key version"):
            await cipher.decrypt(stale, USER_ID)

    @pytest.mark.asyncio
    async def test_decryption_error_never_echoes_the_key(self):
        """NFR-010-02: the failure message must not carry key material."""
        cipher = make_cipher()
        encrypted = await cipher.encrypt(RAW_KEY, USER_ID)
        with pytest.raises(ApiKeyDecryptionError) as exc_info:
            await cipher.decrypt(encrypted, OTHER_USER_ID)
        assert RAW_KEY not in str(exc_info.value)
