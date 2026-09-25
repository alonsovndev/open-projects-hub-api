"""SQLAlchemy implementation of the user API key repository."""

import time

import sqlalchemy.exc
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.ai_config.domain.entities.user_api_key_entity import UserApiKeyEntity
from src.app.features.ai_config.domain.repositories.user_api_key_repository import UserApiKeyRepository
from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider
from src.app.features.ai_config.infrastructure.mappers.user_api_key_mapper import UserApiKeyMapper
from src.app.features.ai_config.infrastructure.models.user_api_key_model import UserApiKeyModel
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger


class UserApiKeyRepositoryImpl(UserApiKeyRepository):
    """
    Postgres-backed storage for user provider keys.

    Log lines here carry the provider and the masked key only — never `encrypted_key`,
    `encryption_nonce`, or anything derived from the plaintext.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Args:
            db_session: SQLAlchemy async session for database operations.
        """
        self.db_session = db_session
        self._log = get_logger(__name__)

    async def find_by_user(self, user_id: EntityId) -> list[UserApiKeyEntity]:
        """Return every key the user has configured, ordered by provider."""
        result = await self.db_session.execute(
            select(UserApiKeyModel)
            .where(UserApiKeyModel.user_id == user_id.value)
            .order_by(UserApiKeyModel.provider.asc())
        )
        return [UserApiKeyMapper.to_entity(model) for model in result.scalars().all()]

    async def find_by_user_and_provider(self, user_id: EntityId, provider: AIProvider) -> UserApiKeyEntity | None:
        """Return the user's key for one provider, or None if they have not configured it."""
        model = await self._get_model(user_id, provider)
        return UserApiKeyMapper.to_entity(model) if model else None

    async def upsert(self, api_key: UserApiKeyEntity) -> UserApiKeyEntity:
        """
        Insert the key, or overwrite the secret on the user's existing row for that provider.

        The overwrite is deliberate: keeping only one row per (user, provider) means a
        rotated key leaves no recoverable copy of the previous secret behind.
        """
        start = time.time()
        try:
            existing = await self._get_model(api_key.user_id, api_key.provider)

            if existing is None:
                model = UserApiKeyMapper.to_model(api_key)
                self.db_session.add(model)
                event_type = "db.insert"
            else:
                existing.encrypted_key = api_key.ciphertext
                existing.encryption_nonce = api_key.nonce
                existing.key_version = api_key.key_version
                existing.masked_key = api_key.masked_key
                existing.last_validated_at = api_key.last_validated_at
                model = existing
                event_type = "db.update"

            await self.db_session.commit()
            await self.db_session.refresh(model)

            self._log.info(
                "Database operation completed",
                extra={
                    "event_type": event_type,
                    "success": True,
                    "duration_ms": (time.time() - start) * 1000,
                    "table": "user_api_keys",
                    "provider": api_key.provider.value,
                    "entity_id": str(model.id),
                },
            )
            return UserApiKeyMapper.to_entity(model)

        except sqlalchemy.exc.SQLAlchemyError:
            await self.db_session.rollback()
            self._log.exception(
                "Failed to save user API key",
                extra={"operation": "upsert", "table": "user_api_keys", "provider": api_key.provider.value},
            )
            raise

    async def delete(self, user_id: EntityId, provider: AIProvider) -> bool:
        """
        Hard-delete the user's key for a provider.

        A real DELETE, not a flag: NFR-010-04 requires removed key material to be
        unrecoverable from storage.
        """
        try:
            result = await self.db_session.execute(
                delete(UserApiKeyModel).where(
                    UserApiKeyModel.user_id == user_id.value,
                    UserApiKeyModel.provider == provider.value,
                )
            )
            await self.db_session.commit()

            deleted = result.rowcount > 0
            self._log.info(
                "Database operation completed",
                extra={
                    "event_type": "db.delete",
                    "success": True,
                    "table": "user_api_keys",
                    "provider": provider.value,
                    "deleted": deleted,
                },
            )
            return deleted

        except sqlalchemy.exc.SQLAlchemyError:
            await self.db_session.rollback()
            self._log.exception(
                "Failed to delete user API key",
                extra={"operation": "delete", "table": "user_api_keys", "provider": provider.value},
            )
            raise

    async def _get_model(self, user_id: EntityId, provider: AIProvider) -> UserApiKeyModel | None:
        result = await self.db_session.execute(
            select(UserApiKeyModel).where(
                UserApiKeyModel.user_id == user_id.value,
                UserApiKeyModel.provider == provider.value,
            )
        )
        return result.scalar_one_or_none()
