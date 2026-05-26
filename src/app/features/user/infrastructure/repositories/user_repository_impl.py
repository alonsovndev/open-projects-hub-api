from typing import Optional, List

from sqlalchemy import select
import sqlalchemy.exc
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.features.user.domain.value_objects.email import Email
from src.app.features.user.infrastructure.models.user_model import UserModel
from src.app.features.user.infrastructure.mappers.user_model_mapper import map_model_to_entity
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger

log = get_logger(__name__)


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

    async def save(self, user: UserEntity) -> Optional[UserEntity]:
        """
        Saves a user entity to the database.
        
        Returns None if a duplicate email exists (infrastructure concern).
        Let the application layer decide how to handle duplicates.

        Args:
            user: UserEntity to save

        Returns:
            UserEntity if saved successfully, None if duplicate email exists

        Raises:
            DatabaseConnectionError: If database connection fails
            Exception: For other unexpected errors
        """
        try:
            result = await self.db_session.execute(select(UserModel).where(UserModel.email == user.email.value))

            if result.scalar_one_or_none():
                log.warning(f"[save] User with email {user.email} already exists - returning None")
                return None

            log.info("[create_user] about to access .value fields")

            user_model = UserModel(
                id=user.id.value,
                email=user.email.value,
                display_name=user.display_name,
                password_hash=user.password_hash,
                role=user.role.value
            )

            self.db_session.add(user_model)
            await self.db_session.commit()
            await self.db_session.refresh(user_model)

            log.info(f"[save] User persisted successfully. id={user_model.id}")
            return map_model_to_entity(user_model)

        except sqlalchemy.exc.IntegrityError as e:
            await self.db_session.rollback()
            log.error(f"[save] IntegrityError while saving user with email {user.email}: {e}")
            # Return None for duplicate email constraint violations
            return None

        except sqlalchemy.exc.OperationalError as db_error:
            await self.db_session.rollback()
            log.error(f"[save] Database connection error: {str(db_error)}")
            raise DatabaseConnectionError("Failed to connect to the database.") from db_error

        except Exception as e:
            await self.db_session.rollback()
            log.error(f"[save] Unexpected error while saving user with email {user.email}: {e}")
            raise

    async def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[UserEntity]:
        """
        Find all users with optional pagination.
        
        Args:
            limit: Maximum number of results (default None = all)
            offset: Number of results to skip (default None = 0)
            
        Returns:
            List of UserEntity objects
            
        Raises:
            DatabaseConnectionError: If database connection fails
            Exception: For other unexpected errors
        """
        try:
            stmt = select(UserModel).order_by(UserModel.created_at.desc())
            
            if offset is not None:
                stmt = stmt.offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)
            
            result = await self.db_session.execute(stmt)
            models = result.scalars().all()
            
            return [map_model_to_entity(model) for model in models]
        
        except sqlalchemy.exc.OperationalError as db_error:
            log.error(f"Database connection error while fetching all users: {str(db_error)}")
            raise DatabaseConnectionError("Failed to connect to the database.") from db_error
        
        except Exception as e:
            log.error(f"Error fetching all users: {str(e)}")
            raise

    async def exists(self, entity_id: EntityId) -> bool:
        """
        Check if a user exists by ID.
        
        Args:
            entity_id: User entity ID
            
        Returns:
            True if user exists, False otherwise
            
        Raises:
            DatabaseConnectionError: If database connection fails
            Exception: For other unexpected errors
        """
        try:
            stmt = select(sqlalchemy.func.count(UserModel.id)).where(UserModel.id == entity_id.value)
            result = await self.db_session.execute(stmt)
            count = result.scalar_one()
            
            return count > 0
        
        except sqlalchemy.exc.OperationalError as db_error:
            log.error(f"Database connection error while checking user existence {entity_id.value}: {str(db_error)}")
            raise DatabaseConnectionError("Failed to connect to the database.") from db_error
        
        except Exception as e:
            log.error(f"Error checking user existence {entity_id.value}: {str(e)}")
            raise

    async def update(self, user: UserEntity) -> Optional[UserEntity]:
        """
        Update an existing user.
        
        Args:
            user: UserEntity to update
            
        Returns:
            Updated UserEntity if successful, None if user not found
            
        Raises:
            DatabaseConnectionError: If database connection fails
            Exception: For other unexpected errors
        """
        try:
            # Check if user exists
            user_model = await self.db_session.get(UserModel, user.id.value)
            
            if not user_model:
                log.warning(f"User {user.id.value} not found for update")
                return None
            
            # Update model fields
            user_model.email = user.email.value
            user_model.display_name = user.display_name
            user_model.password_hash = user.password_hash
            user_model.role = user.role.value
            
            await self.db_session.commit()
            await self.db_session.refresh(user_model)
            
            log.info(f"User {user.id.value} updated successfully")
            return map_model_to_entity(user_model)
        
        except sqlalchemy.exc.IntegrityError as e:
            await self.db_session.rollback()
            log.error(f"IntegrityError while updating user {user.id.value}: {e}")
            # Return None for constraint violations (e.g., duplicate email)
            return None
        
        except sqlalchemy.exc.OperationalError as db_error:
            await self.db_session.rollback()
            log.error(f"Database connection error while updating user {user.id.value}: {str(db_error)}")
            raise DatabaseConnectionError("Failed to connect to the database.") from db_error
        
        except Exception as e:
            await self.db_session.rollback()
            log.error(f"Error updating user {user.id.value}: {str(e)}")
            raise

    async def delete(self, entity_id: EntityId) -> bool:
        """
        Delete a user by ID.
        
        Args:
            entity_id: User entity ID
            
        Returns:
            True if deleted, False if user not found
            
        Raises:
            DatabaseConnectionError: If database connection fails
            Exception: For other unexpected errors
        """
        try:
            user_model = await self.db_session.get(UserModel, entity_id.value)
            
            if not user_model:
                log.info(f"User {entity_id.value} not found for deletion")
                return False
            
            await self.db_session.delete(user_model)
            await self.db_session.commit()
            
            log.info(f"User {entity_id.value} deleted successfully")
            return True
        
        except sqlalchemy.exc.OperationalError as db_error:
            await self.db_session.rollback()
            log.error(f"Database connection error while deleting user {entity_id.value}: {str(db_error)}")
            raise DatabaseConnectionError("Failed to connect to the database.") from db_error
        
        except Exception as e:
            await self.db_session.rollback()
            log.error(f"Error deleting user {entity_id.value}: {str(e)}")
            raise
