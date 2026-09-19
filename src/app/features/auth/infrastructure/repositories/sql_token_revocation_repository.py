from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.auth.infrastructure.models.revoked_refresh_token_model import RevokedRefreshTokenModel
from src.app.shared.infrastructure.security.token_revocation_service import TokenRevocationRepository


class SqlTokenRevocationRepository(TokenRevocationRepository):
    """Postgres-backed refresh-token revocation storage, shared across App Runner instances."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add(self, token_hash: str, expires_at: datetime) -> None:
        model = await self.db_session.get(RevokedRefreshTokenModel, token_hash)
        if model is None:
            self.db_session.add(RevokedRefreshTokenModel(token_hash=token_hash, expires_at=expires_at))
        else:
            model.expires_at = expires_at
        await self.db_session.commit()

    async def contains(self, token_hash: str) -> bool:
        model = await self.db_session.get(RevokedRefreshTokenModel, token_hash)
        if model is None:
            return False
        if model.expires_at <= datetime.now(UTC):
            await self.db_session.delete(model)
            await self.db_session.commit()
            return False
        return True

    async def clear_all(self) -> None:
        await self.db_session.execute(delete(RevokedRefreshTokenModel))
        await self.db_session.commit()

    async def count(self) -> int:
        result = await self.db_session.execute(select(func.count(RevokedRefreshTokenModel.token_hash)))
        return int(result.scalar_one())
