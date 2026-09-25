"""Why a provider call failed, and what the user should do about it (FR-010-10)."""

from enum import StrEnum

from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider


class ProviderFailureReason(StrEnum):
    """
    Provider-agnostic classification of a failed call to an AI provider.

    Each provider reports failures differently; mapping them onto this enum is what lets a
    single set of user-facing messages cover Gemini, OpenAI, and DeepSeek alike.
    """

    INVALID_FORMAT = "invalid_format"
    AUTH_FAILED = "auth_failed"
    QUOTA_EXHAUSTED = "quota_exhausted"
    RATE_LIMITED = "rate_limited"
    NETWORK = "network"

    def guidance(self, provider: AIProvider, retry_after: str | None = None) -> str:
        """
        Actionable, credential-free message naming the provider and the corrective action.

        Wording follows FR-010-10 so the frontend can show it verbatim.

        Args:
            provider: The provider the failure came from.
            retry_after: Human-readable wait, used only by RATE_LIMITED.

        Returns:
            A message safe to return to the user and to log.
        """
        name = provider.display_name
        match self:
            case ProviderFailureReason.INVALID_FORMAT:
                return f"Invalid key format for {name}. Check the key and try again."
            case ProviderFailureReason.AUTH_FAILED:
                return f"API key rejected by {name}. Check your key in Settings."
            case ProviderFailureReason.QUOTA_EXHAUSTED:
                return f"Your {name} quota is exhausted. Upgrade your plan or switch providers."
            case ProviderFailureReason.RATE_LIMITED:
                wait = retry_after or "a moment"
                return f"Rate limit exceeded for {name}. Try again in {wait} or switch providers."
            case ProviderFailureReason.NETWORK:
                return f"Unable to connect to {name}. Check your connection and retry."

    @property
    def prompts_key_update(self) -> bool:
        """
        Whether this failure means the stored key itself is the problem (FR-010-11).

        The frontend uses this to decide between the "update your key" modal and an
        ordinary retry.
        """
        return self in (ProviderFailureReason.AUTH_FAILED, ProviderFailureReason.INVALID_FORMAT)
