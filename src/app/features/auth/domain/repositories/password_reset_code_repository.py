"""Password reset code repository interface."""

from abc import ABC, abstractmethod
from datetime import datetime

from src.app.features.auth.domain.entities.password_reset_code import PasswordResetCode
from src.app.shared.domain.value_objects.entity_id import EntityId


class PasswordResetCodeRepository(ABC):
    """Repository interface for the PasswordResetCode aggregate."""

    @abstractmethod
    async def create(self, reset_code: PasswordResetCode) -> PasswordResetCode:
        """Persist a newly issued reset code."""

    @abstractmethod
    async def find_latest_active_by_user_id(self, user_id: EntityId) -> PasswordResetCode | None:
        """Most recent non-expired, unused code for this user, or None."""

    @abstractmethod
    async def count_created_since(self, user_id: EntityId, since: datetime) -> int:
        """Number of codes issued to this user since the given time (resend rate limit)."""

    @abstractmethod
    async def save(self, reset_code: PasswordResetCode) -> None:
        """Persist attempt_count/used_at changes on an existing code."""

    @abstractmethod
    async def invalidate_active_for_user(self, user_id: EntityId) -> None:
        """Mark every still-active code for this user as used (superseded by a new one)."""
