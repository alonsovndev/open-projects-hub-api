"""Postgres-backed storage for the key validation budget."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import sqlalchemy.exc
from sqlalchemy import case, delete, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.ai_config.domain.repositories.key_validation_attempt_repository import (
    ChargedAttempt,
    KeyValidationAttemptRepository,
)
from src.app.features.ai_config.infrastructure.models.user_api_key_model import ApiKeyValidationAttemptModel
from src.app.shared.logging import get_logger


class SqlKeyValidationAttemptRepository(KeyValidationAttemptRepository):
    """
    Durable validation budget, shared across instances.

    Without this the 5-per-hour limit would be per process, so a user could reset it by
    landing on a different App Runner instance.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Args:
            db_session: SQLAlchemy async session for database operations.
        """
        self.db_session = db_session
        self._log = get_logger(__name__)

    async def charge(self, user_id: str, window_minutes: int) -> ChargedAttempt:
        """
        Record one attempt and return the resulting count.

        A single `INSERT ... ON CONFLICT DO UPDATE ... RETURNING`, so the read, the window
        roll, and the increment happen under one row lock. Splitting this into a SELECT and
        an UPDATE would let concurrent requests each observe the same count and collapse
        into a single charge.
        """
        now = datetime.now(tz=UTC)
        window_opened_before = now - timedelta(minutes=window_minutes)
        table = ApiKeyValidationAttemptModel

        try:
            statement = insert(table).values(
                id=UUID(user_id),
                attempt_count=1,
                window_started_at=now,
            )
            # The stored window is compared inside the statement, not in Python, so the
            # decision to roll or increment is made against the row as locked.
            window_expired = table.window_started_at <= window_opened_before
            statement = statement.on_conflict_do_update(
                index_elements=[table.id],
                set_={
                    "attempt_count": case((window_expired, 1), else_=table.attempt_count + 1),
                    "window_started_at": case((window_expired, now), else_=table.window_started_at),
                    "updated_at": func.now(),
                },
            ).returning(table.attempt_count, table.window_started_at)

            result = await self.db_session.execute(statement)
            attempt_count, window_started_at = result.one()
            await self.db_session.commit()

            return ChargedAttempt(attempt_count=attempt_count, window_started_at=window_started_at)

        except sqlalchemy.exc.SQLAlchemyError:
            await self.db_session.rollback()
            self._log.exception(
                "Failed to record an API key validation attempt",
                extra={"operation": "charge", "table": "api_key_validation_attempts"},
            )
            raise

    async def delete(self, user_id: str) -> None:
        """Drop the user's window, resetting their budget."""
        try:
            await self.db_session.execute(
                delete(ApiKeyValidationAttemptModel).where(ApiKeyValidationAttemptModel.id == UUID(user_id))
            )
            await self.db_session.commit()

        except sqlalchemy.exc.SQLAlchemyError:
            await self.db_session.rollback()
            self._log.exception(
                "Failed to reset the API key validation budget",
                extra={"operation": "delete", "table": "api_key_validation_attempts"},
            )
            raise
