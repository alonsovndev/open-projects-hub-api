from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.auth.infrastructure.models.account_lockout_model import AccountLockoutModel
from src.app.shared.infrastructure.security.account_lockout_service import AccountLockoutRepository, LockoutState


class SqlAccountLockoutRepository(AccountLockoutRepository):
    """Postgres-backed account lockout storage, shared across App Runner instances."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get(self, user_identifier: str) -> LockoutState | None:
        model = await self.db_session.get(AccountLockoutModel, user_identifier)
        if model is None:
            return None
        return LockoutState(
            failed_attempts=model.failed_attempts,
            locked_until=model.locked_until,
            last_attempt=model.last_attempt_at,
        )

    async def save(self, user_identifier: str, state: LockoutState) -> None:
        model = await self.db_session.get(AccountLockoutModel, user_identifier)
        if model is None:
            model = AccountLockoutModel(email=user_identifier)
            self.db_session.add(model)

        model.failed_attempts = state.failed_attempts
        model.locked_until = state.locked_until
        model.last_attempt_at = state.last_attempt
        await self.db_session.commit()

    async def delete(self, user_identifier: str) -> None:
        model = await self.db_session.get(AccountLockoutModel, user_identifier)
        if model is not None:
            await self.db_session.delete(model)
            await self.db_session.commit()

    async def list_all(self) -> dict[str, LockoutState]:
        result = await self.db_session.execute(select(AccountLockoutModel))
        return {
            model.email: LockoutState(
                failed_attempts=model.failed_attempts,
                locked_until=model.locked_until,
                last_attempt=model.last_attempt_at,
            )
            for model in result.scalars().all()
        }
