from typing import Optional, List

import bcrypt
from sqlalchemy import select
import sqlalchemy.exc

from src.app.features.application.exceptions.user_exception import UserAlreadyExistsException
from src.app.features.domain.entities.user_entity import UserEntity
from src.app.features.domain.repositories.user_repository import UserRepository
from src.app.features.domain.value_objects.email import Email
from src.app.features.infrastructure.models.user_model import UserModel
from src.app.features.infrastructure.repository.user_model_mapper import map_model_to_entity
from src.shared.domain.repositories.base_repository import ID, T

from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.domain.value_objects.entity_id import EntityId
from src.shared.utils.log_util import log


class DatabaseConnectionError(Exception):
    """Custom exception to indicate database connection errors."""
    pass


class UserRepositoryImpl(UserRepository):

    def __init__(self, db_session: AsyncSession):
        """
        Initializes the UserRepositoryImpl with a SQLAlchemy AsyncSession.

        Args:
            db_session (AsyncSession): The SQLAlchemy session to use for database operations.
        """
        self.db_session = db_session

    async def find_by_id(self, entity_id: EntityId) -> Optional[UserEntity]:

        try:
            log.info(f"start get user by id: {entity_id.value}")
            user_model: Optional[UserModel] = await self.db_session.get(UserModel, entity_id.value)

            if user_model is None:
                log.info(f"user by id {entity_id.value} not found")
                return None

            log.info(f"completed get user by id {entity_id.value}")

            return map_model_to_entity(user_model)

        except sqlalchemy.exc.OperationalError as db_error:
            log.error(f"Database connection error while finding user by id: {entity_id.value}. Error: {str(db_error)}")
            raise DatabaseConnectionError("Failed to connect to the database.") from db_error

        except Exception as e:
            log.error(f"Error finding user by id: {entity_id.value} Exceptions: {str(e)}")
            raise

    async def find_by_email(self, email: Email) -> Optional[UserEntity]:
        result = await self.db_session.execute(select(UserModel).where(UserModel.email == email.value))

        user_model = result.scalar_one_or_none()

        if user_model is None:
            log.info(f"User with email {email.value} not found.")
            return None

        log.info(f"User with email {email.value} found.")
        return map_model_to_entity(user_model)

    async def find_by_name(self, record: str) -> Optional[UserEntity]:
        pass

    async def save(self, user: UserEntity) -> UserEntity:
        try:
            result = await self.db_session.execute(select(UserModel).where(UserModel.email == user.email.value))

            if result.scalar_one_or_none():
                log.warning(f"[save] User with email {user.email} already exists")
                raise UserAlreadyExistsException(user.email.value)

            log.info("[create_user] about to access .value fields")

            user_model = UserModel(id=user.id.value, email=user.email.value, first_name=user.first_name, last_name=user.last_name, password_hash=user.password_hash,)

            self.db_session.add(user_model)
            await self.db_session.commit()
            await self.db_session.refresh(user_model)

            log.info(f"[save] User persisted successfully. id={user_model.id}")
            return map_model_to_entity(user_model)

        except sqlalchemy.exc.IntegrityError as e:
            await self.db_session.rollback()

            log.error(f"[save] IntegrityError while saving user with email {user.email}: {e}")
            raise UserAlreadyExistsException(user.email.value) from e

        except Exception as e:
            await self.db_session.rollback()
            log.error(f"[save] Unexpected error while saving user with email {user.email}: {e}")
            raise

    async def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        pass

    async def exists(self, entity_id: ID) -> bool:
        pass

    async def update(self, entity: T) -> Optional[T]:
        pass

    async def delete(self, entity_id: ID) -> bool:
        pass