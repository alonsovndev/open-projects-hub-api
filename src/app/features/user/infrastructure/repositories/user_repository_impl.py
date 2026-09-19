import time

import sqlalchemy.exc
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.features.user.infrastructure.mappers.user_mapper import UserMapper
from src.app.features.user.infrastructure.models.user_model import UserModel
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger


class DatabaseConnectionError(Exception):
    """Custom exception to indicate database connection errors."""


class UserRepositoryImpl(UserRepository):
    def __init__(self, db_session: AsyncSession):
        """
        Initializes the UserRepositoryImpl with a SQLAlchemy AsyncSession.

        Args:
            db_session (AsyncSession): The SQLAlchemy session to use for database operations.
        """
        self.db_session = db_session
        self._log = get_logger(__name__)

    async def find_by_id(self, entity_id: EntityId) -> UserEntity | None:
        try:
            self._log.info(f"start get user by id: {entity_id.value}")
            user_model: UserModel | None = await self.db_session.get(UserModel, entity_id.value)

            if user_model is None:
                self._log.info(f"user by id {entity_id.value} not found")
                return None

            self._log.info(f"completed get user by id {entity_id.value}")

            return UserMapper.to_entity(user_model)

        except sqlalchemy.exc.OperationalError as db_error:
            self._log.exception("Database connection error", extra={"operation": "find_by_id", "table": "users"})
            raise DatabaseConnectionError("Failed to connect to the database.") from db_error

        except Exception:
            self._log.exception("Error finding user by id", extra={"operation": "find_by_id", "table": "users"})
            raise

    async def find_by_email(self, email: Email) -> UserEntity | None:
        try:
            result = await self.db_session.execute(select(UserModel).where(UserModel.email == email.value))
            user_model = result.scalar_one_or_none()

            if user_model is None:
                self._log.info(
                    "User with email not found",
                    extra={"email": email.value, "operation": "find_by_email", "table": "users"},
                )
                return None

            self._log.info(
                "User with email found", extra={"email": email.value, "operation": "find_by_email", "table": "users"}
            )
            return UserMapper.to_entity(user_model)

        except sqlalchemy.exc.OperationalError as db_error:
            self._log.exception("Database connection error", extra={"operation": "find_by_email", "table": "users"})
            raise DatabaseConnectionError("Failed to connect to the database.") from db_error

        except Exception:
            self._log.exception("Error finding user by email", extra={"operation": "find_by_email", "table": "users"})
            raise

    async def find_by_name(self, record: str) -> UserEntity | None:
        pass

    async def save(self, user: UserEntity) -> UserEntity | None:
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
        start = time.time()
        try:
            result = await self.db_session.execute(select(UserModel).where(UserModel.email == user.email.value))

            if result.scalar_one_or_none():
                self._log.warning(
                    "User with email already exists - returning None",
                    extra={"email": str(user.email), "operation": "save", "table": "users"},
                )
                return None

            user_model = UserMapper.to_model(user)

            self.db_session.add(user_model)
            await self.db_session.commit()
            await self.db_session.refresh(user_model)

            duration = (time.time() - start) * 1000
            self._log.info(
                "Database operation completed",
                extra={
                    "event_type": "db.insert",
                    "success": True,
                    "duration_ms": duration,
                    "table": "users",
                    "entity_id": str(user.id.value),
                },
            )
            return UserMapper.to_entity(user_model)

        except sqlalchemy.exc.IntegrityError:
            await self.db_session.rollback()
            self._log.exception(
                "IntegrityError while saving user with email", extra={"operation": "save", "table": "users"}
            )
            # Return None for duplicate email constraint violations
            return None

        except sqlalchemy.exc.OperationalError as db_error:
            await self.db_session.rollback()
            self._log.exception("Database connection error", extra={"operation": "save", "table": "users"})
            raise DatabaseConnectionError("Failed to connect to the database.") from db_error

        except Exception:
            await self.db_session.rollback()
            self._log.exception("Unexpected error while saving user", extra={"operation": "save", "table": "users"})
            raise

    async def find_all(self, limit: int | None = None, offset: int | None = None) -> list[UserEntity]:
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

            return [UserMapper.to_entity(model) for model in models]

        except sqlalchemy.exc.OperationalError as db_error:
            self._log.exception("Database connection error", extra={"operation": "find_all", "table": "users"})
            raise DatabaseConnectionError("Failed to connect to the database.") from db_error

        except Exception:
            self._log.exception("Error fetching all users", extra={"operation": "find_all", "table": "users"})
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
            return bool(int(result.scalar_one()))

        except sqlalchemy.exc.OperationalError as db_error:
            self._log.exception("Database connection error", extra={"operation": "exists", "table": "users"})
            raise DatabaseConnectionError("Failed to connect to the database.") from db_error

        except Exception:
            self._log.exception("Error checking user existence", extra={"operation": "exists", "table": "users"})
            raise

    async def update(self, user: UserEntity) -> UserEntity | None:
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
        start = time.time()
        try:
            # Check if user exists
            user_model = await self.db_session.get(UserModel, user.id.value)

            if not user_model:
                self._log.warning(
                    "User not found for update",
                    extra={"user_id": str(user.id.value), "operation": "update", "table": "users"},
                )
                return None

            # Update model fields
            user_model.email = user.email.value
            user_model.display_name = user.display_name
            user_model.password_hash = user.password_hash
            user_model.role = user.role.value
            user_model.token_version = user.token_version

            await self.db_session.commit()
            await self.db_session.refresh(user_model)

            duration = (time.time() - start) * 1000
            self._log.info(
                "Database operation completed",
                extra={
                    "event_type": "db.update",
                    "success": True,
                    "duration_ms": duration,
                    "table": "users",
                    "entity_id": str(user.id.value),
                },
            )
            return UserMapper.to_entity(user_model)

        except sqlalchemy.exc.IntegrityError:
            await self.db_session.rollback()
            self._log.exception("IntegrityError while updating user", extra={"operation": "update", "table": "users"})
            # Return None for constraint violations (e.g., duplicate email)
            return None

        except sqlalchemy.exc.OperationalError as db_error:
            await self.db_session.rollback()
            self._log.exception("Database connection error", extra={"operation": "update", "table": "users"})
            raise DatabaseConnectionError("Failed to connect to the database.") from db_error

        except Exception:
            await self.db_session.rollback()
            self._log.exception("Error updating user", extra={"operation": "update", "table": "users"})
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
        start = time.time()
        try:
            user_model = await self.db_session.get(UserModel, entity_id.value)

            if not user_model:
                self._log.info(
                    "User not found for deletion",
                    extra={"user_id": str(entity_id.value), "operation": "delete", "table": "users"},
                )
                return False

            await self.db_session.delete(user_model)
            await self.db_session.commit()

            duration = (time.time() - start) * 1000
            self._log.info(
                "Database operation completed",
                extra={
                    "event_type": "db.delete",
                    "success": True,
                    "duration_ms": duration,
                    "table": "users",
                    "entity_id": str(entity_id.value),
                },
            )
            return True

        except sqlalchemy.exc.OperationalError as db_error:
            await self.db_session.rollback()
            self._log.exception("Database connection error", extra={"operation": "delete", "table": "users"})
            raise DatabaseConnectionError("Failed to connect to the database.") from db_error

        except Exception:
            await self.db_session.rollback()
            self._log.exception("Error deleting user", extra={"operation": "delete", "table": "users"})
            raise
