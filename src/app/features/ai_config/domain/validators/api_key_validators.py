"""Format checks applied to a provider API key before it is sent anywhere (FR-010-05)."""

from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider
from src.app.shared.domain.exceptions.domain_exceptions import ValidationError


# Shortest plausible key across the three providers. The point is to reject obvious
# typos and empty submissions locally rather than spend a validation attempt on them.
MIN_KEY_LENGTH = 20
MAX_KEY_LENGTH = 512

# Prefixes the providers document for their keys. Checked case-sensitively because
# that is how the providers issue them.
_EXPECTED_PREFIXES: dict[AIProvider, tuple[str, ...]] = {
    AIProvider.GEMINI: ("AIza",),
    AIProvider.OPENAI: ("sk-",),
    AIProvider.DEEPSEEK: ("sk-",),
}


class ApiKeyValidators:
    """Local, zero-cost validation run before the rate-limited provider round-trip."""

    @staticmethod
    def validate_format(raw_key: str, provider: AIProvider) -> None:
        """
        Check a key looks like one this provider issues.

        A pass here means the key is worth spending a validation attempt on, not that the
        provider will accept it.

        Args:
            raw_key: The raw provider key.
            provider: The provider the key is claimed to belong to.

        Raises:
            ValidationError: If the key is empty, the wrong length, contains whitespace,
                or lacks the provider's documented prefix.
        """
        key = raw_key.strip()

        if not key:
            raise ValidationError("Invalid key format: the API key is empty.")

        if len(key) < MIN_KEY_LENGTH or len(key) > MAX_KEY_LENGTH:
            raise ValidationError(
                f"Invalid key format: expected between {MIN_KEY_LENGTH} and {MAX_KEY_LENGTH} characters."
            )

        if any(character.isspace() for character in key):
            raise ValidationError("Invalid key format: the API key contains whitespace.")

        prefixes = _EXPECTED_PREFIXES[provider]
        if not key.startswith(prefixes):
            expected = " or ".join(f"'{prefix}'" for prefix in prefixes)
            raise ValidationError(f"Invalid key format: a {provider.display_name} key starts with {expected}.")
