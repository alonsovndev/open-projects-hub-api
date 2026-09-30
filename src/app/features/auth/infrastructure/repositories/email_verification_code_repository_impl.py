from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.auth.domain.entities.email_verification_code import EmailVerificationCode
from src.app.features.auth.domain.repositories.email_verification_code_repository import EmailVerificationCodeRepository
from src.app.features.auth.infrastructure.models.email_verification_code_model import EmailVerificationCodeModel
from src.app.shared.domain.value_objects.entity_id import EntityId


class EmailVerificationCodeRepositoryImpl(EmailVerificationCodeRepository):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create(self, verification_code: EmailVerificationCode) -> EmailVerificationCode:
        model = EmailVerificationCodeModel(
            id=verification_code.id.value,
            user_id=verification_code.user_id.value,
            code_hash=verification_code.code_hash,
            expires_at=verification_code.expires_at,
            attempt_count=verification_code.attempt_count,
            used_at=verification_code.used_at,
        )
        self.db_session.add(model)
        await self.db_session.commit()
        await self.db_session.refresh(model)
        return self._to_entity(model)

    async def find_latest_active_by_user_id(self, user_id: EntityId) -> EmailVerificationCode | None:
        now = datetime.now(UTC)
        stmt = (
            select(EmailVerificationCodeModel)
            .where(
                EmailVerificationCodeModel.user_id == user_id.value,
                EmailVerificationCodeModel.used_at.is_(None),
                EmailVerificationCodeModel.expires_at > now,
            )
            .order_by(EmailVerificationCodeModel.created_at.desc())
            .limit(1)
        )
        result = await self.db_session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def count_created_since(self, user_id: EntityId, since: datetime) -> int:
        stmt = select(func.count(EmailVerificationCodeModel.id)).where(
            EmailVerificationCodeModel.user_id == user_id.value,
            EmailVerificationCodeModel.created_at >= since,
        )
        result = await self.db_session.execute(stmt)
        return int(result.scalar_one())

    async def save(self, verification_code: EmailVerificationCode) -> None:
        model = await self.db_session.get(EmailVerificationCodeModel, verification_code.id.value)
        if model is None:
            return
        model.attempt_count = verification_code.attempt_count
        model.used_at = verification_code.used_at
        await self.db_session.commit()

    async def invalidate_active_for_user(self, user_id: EntityId) -> None:
        now = datetime.now(UTC)
        stmt = (
            update(EmailVerificationCodeModel)
            .where(EmailVerificationCodeModel.user_id == user_id.value, EmailVerificationCodeModel.used_at.is_(None))
            .values(used_at=now)
        )
        await self.db_session.execute(stmt)
        await self.db_session.commit()

    @staticmethod
    def _to_entity(model: EmailVerificationCodeModel) -> EmailVerificationCode:
        return EmailVerificationCode(
            id=EntityId(model.id),
            user_id=EntityId(model.user_id),
            code_hash=model.code_hash,
            expires_at=model.expires_at,
            attempt_count=model.attempt_count,
            used_at=model.used_at,
            created_at=model.created_at,
        )
