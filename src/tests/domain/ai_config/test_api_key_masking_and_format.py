"""Tests for API key masking (FR-010-07) and format validation (FR-010-05)."""

import pytest

from src.app.features.ai_config.domain.services.api_key_masker import ApiKeyMasker
from src.app.features.ai_config.domain.validators.api_key_validators import MAX_KEY_LENGTH, ApiKeyValidators
from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider
from src.app.shared.domain.exceptions.domain_exceptions import ValidationError


class TestApiKeyMasker:
    """The mask is the only representation of a key that leaves the backend."""

    def test_keeps_a_recognizable_head_and_the_last_four_characters(self):
        assert ApiKeyMasker.mask("sk-proj-abcdefghijklmnop1234") == "sk-proj***...1234"

    def test_masks_a_gemini_key(self):
        assert ApiKeyMasker.mask("AIzaSyD-abcdefghijklmnopqrs9876") == "AIzaSyD***...9876"

    def test_never_reveals_more_than_the_first_seven_and_last_four(self):
        raw = "sk-proj-SECRETMIDDLESECTION-9999"
        masked = ApiKeyMasker.mask(raw)
        assert "SECRETMIDDLESECTION" not in masked
        assert raw not in masked

    @pytest.mark.parametrize("short_key", ["", "sk-", "sk-abc123", "sk-proj-abc"])
    def test_fully_masks_keys_too_short_to_split_safely(self, short_key):
        """A short key has no safe head and tail, so none of it is shown."""
        assert ApiKeyMasker.mask(short_key) == "***"

    def test_ignores_surrounding_whitespace(self):
        assert ApiKeyMasker.mask("  sk-proj-abcdefghijklmnop1234  ") == "sk-proj***...1234"


class TestApiKeyFormatValidation:
    """Local checks that spare an obvious typo a rate-limited provider round-trip."""

    @pytest.mark.parametrize(
        ("provider", "key"),
        [
            (AIProvider.OPENAI, "sk-proj-abcdefghijklmnopqrstuv"),
            (AIProvider.DEEPSEEK, "sk-abcdefghijklmnopqrstuvwxyz"),
            (AIProvider.GEMINI, "AIzaSyD-abcdefghijklmnopqrstu"),
        ],
    )
    def test_accepts_a_well_formed_key(self, provider, key):
        ApiKeyValidators.validate_format(key, provider)

    @pytest.mark.parametrize("provider", list(AIProvider))
    def test_rejects_an_empty_key(self, provider):
        with pytest.raises(ValidationError, match="empty"):
            ApiKeyValidators.validate_format("   ", provider)

    def test_rejects_a_key_that_is_too_short(self):
        with pytest.raises(ValidationError, match="characters"):
            ApiKeyValidators.validate_format("sk-short", AIProvider.OPENAI)

    def test_rejects_a_key_that_is_too_long(self):
        with pytest.raises(ValidationError, match="characters"):
            ApiKeyValidators.validate_format("sk-" + "a" * MAX_KEY_LENGTH, AIProvider.OPENAI)

    def test_rejects_a_key_containing_whitespace(self):
        with pytest.raises(ValidationError, match="whitespace"):
            ApiKeyValidators.validate_format("sk-proj-abcdefg hijklmnopqrs", AIProvider.OPENAI)

    def test_rejects_a_gemini_key_pasted_into_the_openai_field(self):
        with pytest.raises(ValidationError, match="starts with"):
            ApiKeyValidators.validate_format("AIzaSyD-abcdefghijklmnopqrstu", AIProvider.OPENAI)

    def test_rejects_an_openai_key_pasted_into_the_gemini_field(self):
        with pytest.raises(ValidationError, match="starts with"):
            ApiKeyValidators.validate_format("sk-proj-abcdefghijklmnopqrstuv", AIProvider.GEMINI)

    def test_error_message_never_echoes_the_key(self):
        """NFR-010-02: even a rejection must not repeat what was submitted."""
        secret = "sk-proj-SUPERSECRETVALUE with a space"
        with pytest.raises(ValidationError) as exc_info:
            ApiKeyValidators.validate_format(secret, AIProvider.OPENAI)
        assert "SUPERSECRETVALUE" not in str(exc_info.value)
