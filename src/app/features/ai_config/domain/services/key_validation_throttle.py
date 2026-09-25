"""Per-user budget for API key validation attempts (NFR-010-03)."""

from datetime import UTC, datetime, timedelta

from src.app.features.ai_config.domain.exceptions.ai_config_exceptions import KeyValidationRateLimitedError
from src.app.features.ai_config.domain.repositories.key_validation_attempt_repository import (
    KeyValidationAttemptRepository,
)


class KeyValidationThrottle:
    """
    Caps how often one user may ask us to test a key against a provider.

    Every validation is an outbound call to a third party on the platform's dime, and an
    unbounded one would let a single account probe provider APIs through us. The budget is
    therefore per user, not per IP: slowapi's IP-keyed limiter would neither stop one
    account from probing nor spare users sharing an address.

    The window is fixed rather than sliding — it starts on the first attempt and resets
    once an hour has passed — which keeps the stored state to a counter and a timestamp.

    All the concurrency safety lives in the repository's atomic charge. This class is
    deliberately free of in-process locking: a lock here would be theatre, since the
    composition root builds a fresh throttle per request and multiple instances serve
    traffic in production.
    """

    MAX_ATTEMPTS = 5
    WINDOW_MINUTES = 60

    def __init__(self, repository: KeyValidationAttemptRepository):
        """
        Args:
            repository: Storage backend providing the atomic charge.
        """
        self._repository = repository

    async def consume(self, user_id: str) -> None:
        """
        Charge one validation attempt against the user's budget.

        Args:
            user_id: The user's UUID string.

        Raises:
            KeyValidationRateLimitedError: If the budget for the current window is spent.
        """
        charged = await self._repository.charge(user_id, self.WINDOW_MINUTES)

        if charged.attempt_count > self.MAX_ATTEMPTS:
            resets_at = charged.window_started_at + timedelta(minutes=self.WINDOW_MINUTES)
            remaining = (resets_at - datetime.now(tz=UTC)).total_seconds()
            raise KeyValidationRateLimitedError(retry_after_seconds=max(1, int(remaining)))

    async def reset(self, user_id: str) -> None:
        """Clear the user's budget. Used by tests and administrative tooling."""
        await self._repository.delete(user_id)
