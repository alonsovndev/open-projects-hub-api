"""Domain entity for password reset codes."""

from dataclasses import dataclass
from datetime import UTC, datetime

from src.app.shared.domain.value_objects.entity_id import EntityId


@dataclass
class PasswordResetCode:
    """A single-use, time-bound code issued to reset a user's password."""

    MAX_VALIDATION_ATTEMPTS = 5

    id: EntityId
    user_id: EntityId
    code_hash: str
    expires_at: datetime
    attempt_count: int = 0
    used_at: datetime | None = None
    created_at: datetime | None = None

    def is_expired(self, now: datetime | None = None) -> bool:
        return (now or datetime.now(UTC)) >= self.expires_at

    def is_rate_limited(self) -> bool:
        return self.attempt_count >= self.MAX_VALIDATION_ATTEMPTS

    def record_failed_attempt(self) -> None:
        self.attempt_count += 1

    def mark_used(self, now: datetime | None = None) -> None:
        self.used_at = now or datetime.now(UTC)
