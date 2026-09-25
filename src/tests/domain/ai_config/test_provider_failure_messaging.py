"""Tests for provider error messaging (FR-010-10) and the key-update prompt (FR-010-11)."""

import pytest

from src.app.features.ai_config.domain.exceptions.ai_config_exceptions import ApiKeyRejectedError
from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider, RefinementProvider
from src.app.features.ai_config.domain.value_objects.provider_failure_reason import ProviderFailureReason


class TestProviderFailureGuidance:
    """Every failure class must map to an actionable, provider-named message."""

    @pytest.mark.parametrize("reason", list(ProviderFailureReason))
    @pytest.mark.parametrize("provider", list(AIProvider))
    def test_every_reason_names_the_provider_and_an_action(self, reason, provider):
        message = reason.guidance(provider)
        assert provider.display_name in message
        assert message.endswith(".")

    def test_quota_exhausted_matches_the_specified_wording(self):
        message = ProviderFailureReason.QUOTA_EXHAUSTED.guidance(AIProvider.OPENAI)
        assert message == "Your OpenAI quota is exhausted. Upgrade your plan or switch providers."

    def test_auth_failed_points_the_user_at_settings(self):
        message = ProviderFailureReason.AUTH_FAILED.guidance(AIProvider.GEMINI)
        assert message == "API key rejected by Gemini. Check your key in Settings."

    def test_network_error_suggests_checking_the_connection(self):
        message = ProviderFailureReason.NETWORK.guidance(AIProvider.DEEPSEEK)
        assert message == "Unable to connect to DeepSeek. Check your connection and retry."

    def test_rate_limit_includes_the_provider_supplied_wait(self):
        message = ProviderFailureReason.RATE_LIMITED.guidance(AIProvider.OPENAI, retry_after="30 seconds")
        assert "30 seconds" in message

    def test_rate_limit_stays_readable_without_a_wait(self):
        message = ProviderFailureReason.RATE_LIMITED.guidance(AIProvider.OPENAI)
        assert "a moment" in message

    @pytest.mark.parametrize(
        ("reason", "expected"),
        [
            (ProviderFailureReason.AUTH_FAILED, True),
            (ProviderFailureReason.INVALID_FORMAT, True),
            (ProviderFailureReason.QUOTA_EXHAUSTED, False),
            (ProviderFailureReason.RATE_LIMITED, False),
            (ProviderFailureReason.NETWORK, False),
        ],
    )
    def test_only_key_problems_prompt_a_key_update(self, reason, expected):
        """FR-010-11's modal is for a bad key, not for a provider outage or a spent quota."""
        assert reason.prompts_key_update is expected


class TestApiKeyRejectedError:
    """The exception carries the guidance the API returns verbatim."""

    def test_message_is_the_reason_guidance(self):
        error = ApiKeyRejectedError(AIProvider.OPENAI, ProviderFailureReason.AUTH_FAILED)
        assert str(error) == "API key rejected by OpenAI. Check your key in Settings."

    def test_retains_the_reason_for_the_handler_to_classify(self):
        error = ApiKeyRejectedError(AIProvider.GEMINI, ProviderFailureReason.QUOTA_EXHAUSTED)
        assert error.reason is ProviderFailureReason.QUOTA_EXHAUSTED
        assert error.provider is AIProvider.GEMINI


class TestRefinementProvider:
    """Platform selection is distinguishable from a user-key selection."""

    def test_platform_is_the_only_credit_spending_selection(self):
        assert RefinementProvider.PLATFORM.is_platform
        for provider in (RefinementProvider.GEMINI, RefinementProvider.OPENAI, RefinementProvider.DEEPSEEK):
            assert not provider.is_platform

    @pytest.mark.parametrize(
        ("selection", "expected"),
        [
            (RefinementProvider.GEMINI, AIProvider.GEMINI),
            (RefinementProvider.OPENAI, AIProvider.OPENAI),
            (RefinementProvider.DEEPSEEK, AIProvider.DEEPSEEK),
        ],
    )
    def test_maps_onto_the_user_key_provider(self, selection, expected):
        assert selection.to_api_provider() is expected

    def test_platform_has_no_user_key_behind_it(self):
        with pytest.raises(ValueError, match="not backed by a user API key"):
            RefinementProvider.PLATFORM.to_api_provider()
