"""AI credit and API key domain exceptions."""

from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider
from src.app.features.ai_config.domain.value_objects.provider_failure_reason import ProviderFailureReason
from src.app.shared.domain.exceptions.domain_exceptions import DomainError


class ApiKeyNotFoundError(DomainError):
    """
    Raised when an operation targets a provider the user has no key for.

    Maps to HTTP 404.
    """

    def __init__(self, provider: AIProvider):
        self.provider = provider
        super().__init__(f"No {provider.display_name} API key is configured.")


class ApiKeyRejectedError(DomainError):
    """
    Raised when a provider refuses a key, on save or mid-refinement.

    Maps to HTTP 422. `reason` drives both the message and whether the frontend should
    prompt the user to update the key (FR-010-11).
    """

    def __init__(
        self,
        provider: AIProvider,
        reason: ProviderFailureReason,
        retry_after: str | None = None,
    ):
        self.provider = provider
        self.reason = reason
        self.retry_after = retry_after
        super().__init__(reason.guidance(provider, retry_after))


class KeyValidationRateLimitedError(DomainError):
    """
    Raised when a user exceeds the key-validation budget (NFR-010-03).

    Maps to HTTP 429. Validation calls hit third-party APIs, so the limit is per user
    rather than per IP — an IP limit would neither stop a single account from probing
    providers nor protect a user behind a shared address.
    """

    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds
        minutes = max(1, round(retry_after_seconds / 60))
        super().__init__(f"Validation limit reached. Try again in {minutes} minute(s).")
