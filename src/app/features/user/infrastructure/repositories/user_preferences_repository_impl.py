"""
UserPreferencesRepository implementation using SQLAlchemy.
"""
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from src.app.features.user.domain.entities.user_preferences_entity import UserPreferencesEntity
from src.app.features.user.domain.repositories.user_preferences_repository import UserPreferencesRepository
from src.app.features.user.infrastructure.mappers import user_preferences_mapper
from src.app.features.user.infrastructure.models.user_preferences_model import UserPreferencesModel
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger

log = get_logger(__name__)


class UserPreferencesRepositoryImpl(UserPreferencesRepository):
    """SQLAlchemy implementation of UserPreferencesRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_user_id(self, user_id: EntityId) -> Optional[UserPreferencesEntity]:
        """
        Find preferences by user ID.
        
        Args:
            user_id: User entity ID
            
        Returns:
            UserPreferencesEntity if found, None otherwise
            
        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(UserPreferencesModel).where(
                UserPreferencesModel.user_id == user_id.value
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                return user_preferences_mapper.to_entity(model)
            return None

        except OperationalError as e:
            log.error(
                f"Database connection error while finding preferences for user {user_id.value}: {e}",
                exc_info=True
            )
            raise
        except SQLAlchemyError as e:
            log.error(
                f"Database error while finding preferences for user {user_id.value}: {e}",
                exc_info=True
            )
            raise

    async def save(self, preferences: UserPreferencesEntity) -> Optional[UserPreferencesEntity]:
        """
        Save or update user preferences.
        
        Args:
            preferences: UserPreferencesEntity to save
            
        Returns:
            Saved UserPreferencesEntity
            
        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            # Check if preferences already exist
            stmt = select(UserPreferencesModel).where(
                UserPreferencesModel.user_id == preferences.user_id.value
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing preferences
                updated_model = user_preferences_mapper.update_model_from_entity(existing, preferences)
                await self.session.flush()
                await self.session.commit()
                return user_preferences_mapper.to_entity(updated_model)
            else:
                # Create new preferences
                new_model = user_preferences_mapper.to_model(preferences)
                self.session.add(new_model)
                await self.session.flush()
                await self.session.commit()
                return user_preferences_mapper.to_entity(new_model)

        except OperationalError as e:
            await self.session.rollback()
            log.error(
                f"Database connection error while saving preferences for user {preferences.user_id.value}: {e}",
                exc_info=True
            )
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error(
                f"Database error while saving preferences for user {preferences.user_id.value}: {e}",
                exc_info=True
            )
            raise

    async def delete_by_user_id(self, user_id: EntityId) -> bool:
        """
        Delete preferences by user ID.
        
        Args:
            user_id: User entity ID
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = delete(UserPreferencesModel).where(
                UserPreferencesModel.user_id == user_id.value
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0

        except OperationalError as e:
            await self.session.rollback()
            log.error(
                f"Database connection error while deleting preferences for user {user_id.value}: {e}",
                exc_info=True
            )
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error(
                f"Database error while deleting preferences for user {user_id.value}: {e}",
                exc_info=True
            )
            raise
