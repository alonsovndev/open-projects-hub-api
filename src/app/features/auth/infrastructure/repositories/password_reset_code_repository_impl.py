from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.auth.domain.entities.password_reset_code import PasswordResetCode
from src.app.features.auth.domain.repositories.password_reset_code_repository import PasswordResetCodeRepository
from src.app.features.auth.infrastructure.models.password_reset_code_model import PasswordResetCodeModel
from src.app.shared.domain.value_objects.entity_id import EntityId


class PasswordResetCodeRepositoryImpl(PasswordResetCodeRepository):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create(self, reset_code: PasswordResetCode) -> PasswordResetCode:
        model = PasswordResetCodeModel(
            id=reset_code.id.value,
            user_id=reset_code.user_id.value,
            code_hash=reset_code.code_hash,
            expires_at=reset_code.expires_at,
            attempt_count=reset_code.attempt_count,
            used_at=reset_code.used_at,
        )
        self.db_session.add(model)
        await self.db_session.commit()
        await self.db_session.refresh(model)
        return self._to_entity(model)

    async def find_latest_active_by_user_id(self, user_id: EntityId) -> PasswordResetCode | None:
        now = datetime.now(UTC)
        stmt = (
            select(PasswordResetCodeModel)
            .where(
                PasswordResetCodeModel.user_id == user_id.value,
                PasswordResetCodeModel.used_at.is_(None),
                PasswordResetCodeModel.expires_at > now,
            )
            .order_by(PasswordResetCodeModel.created_at.desc())
            .limit(1)
        )
        result = await self.db_session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def count_created_since(self, user_id: EntityId, since: datetime) -> int:
        stmt = select(func.count(PasswordResetCodeModel.id)).where(
            PasswordResetCodeModel.user_id == user_id.value,
            PasswordResetCodeModel.created_at >= since,
        )
        result = await self.db_session.execute(stmt)
        return int(result.scalar_one())

    async def save(self, reset_code: PasswordResetCode) -> None:
        model = await self.db_session.get(PasswordResetCodeModel, reset_code.id.value)
        if model is None:
            return
        model.attempt_count = reset_code.attempt_count
        model.used_at = reset_code.used_at
        await self.db_session.commit()

    async def invalidate_active_for_user(self, user_id: EntityId) -> None:
        now = datetime.now(UTC)
        stmt = (
            update(PasswordResetCodeModel)
            .where(PasswordResetCodeModel.user_id == user_id.value, PasswordResetCodeModel.used_at.is_(None))
            .values(used_at=now)
        )
        await self.db_session.execute(stmt)
        await self.db_session.commit()

    @staticmethod
    def _to_entity(model: PasswordResetCodeModel) -> PasswordResetCode:
        return PasswordResetCode(
            id=EntityId(model.id),
            user_id=EntityId(model.user_id),
            code_hash=model.code_hash,
            expires_at=model.expires_at,
            attempt_count=model.attempt_count,
            used_at=model.used_at,
            created_at=model.created_at,
        )
