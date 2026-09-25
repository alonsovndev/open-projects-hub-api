"""AI provider identifiers for user-supplied keys and refinement provider selection."""

from enum import StrEnum


class AIProvider(StrEnum):
    """
    A third-party AI provider a user can hold their own API key for.

    Values match the `provider` enum in the API contract and the Postgres `aiprovider` type.
    """

    GEMINI = "gemini"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"

    @property
    def display_name(self) -> str:
        """Provider name as written in user-facing messages."""
        match self:
            case AIProvider.GEMINI:
                return "Gemini"
            case AIProvider.OPENAI:
                return "OpenAI"
            case AIProvider.DEEPSEEK:
                return "DeepSeek"


class RefinementProvider(StrEnum):
    """
    What a single refinement run should be billed against.

    `PLATFORM` spends one of the user's free credits on the platform's own key; every other
    value spends the user's own provider quota and leaves the credit balance untouched.
    """

    PLATFORM = "platform"
    GEMINI = "gemini"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"

    @property
    def is_platform(self) -> bool:
        """True when this run consumes a platform credit rather than a user's own key."""
        return self is RefinementProvider.PLATFORM

    def to_api_provider(self) -> AIProvider:
        """
        The user-key provider this selection maps to.

        Raises:
            ValueError: If called on PLATFORM, which has no user key behind it.
        """
        if self.is_platform:
            raise ValueError("PLATFORM is not backed by a user API key")
        return AIProvider(self.value)
