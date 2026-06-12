"""Story repository implementation using SQLAlchemy."""

import time
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.stories.infrastructure.mappers.story_mapper import StoryMapper
from src.app.features.stories.infrastructure.models.story_model import StoryModel
from src.app.shared.logging import TechnicalLogger, get_logger


class StoryRepositoryImpl(StoryRepository):
    """SQLAlchemy implementation of StoryRepository."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session
        self._log = TechnicalLogger(get_logger(__name__), component="database")

    async def find_by_id(self, story_id: UUID) -> StoryEntity | None:
        """
        Find story by ID.

        Args:
            story_id: Story UUID

        Returns:
            StoryEntity if found, None otherwise

        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(StoryModel).where(StoryModel.id == story_id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                return StoryMapper.to_entity(model)
            return None

        except OperationalError as e:
            self._log.connection_error("database", error=e, operation="find_by_id", table="stories")
            raise
        except SQLAlchemyError as e:
            self._log.error(
                f"Database error while fetching story {story_id}", error=e, operation="find_by_id", table="stories"
            )
            raise

    async def find_all(
        self,
        limit: int = 20,
        offset: int = 0,
        project_id: UUID | None = None,
        status: str | None = None,
        priority: str | None = None,
        assigned_to: UUID | None = None,
    ) -> list[StoryEntity]:
        """
        Find all stories with pagination and optional filtering.

        Args:
            limit: Maximum number of results (default 20)
            offset: Number of results to skip (default 0)
            project_id: Optional project filter
            status: Optional status filter (todo, in_progress, done)
            priority: Optional priority filter (low, medium, high)
            assigned_to: Optional assigned user filter

        Returns:
            List of StoryEntity objects

        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(StoryModel)

            if project_id:
                stmt = stmt.where(StoryModel.project_id == project_id)
            if status:
                stmt = stmt.where(StoryModel.status == status)
            if priority:
                stmt = stmt.where(StoryModel.priority == priority)
            if assigned_to:
                stmt = stmt.where(StoryModel.assigned_to == assigned_to)

            stmt = stmt.order_by(StoryModel.created_at.desc())
            stmt = stmt.limit(limit).offset(offset)

            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [StoryMapper.to_entity(model) for model in models]

        except OperationalError as e:
            self._log.connection_error("database", error=e, operation="find_all", table="stories")
            raise
        except SQLAlchemyError as e:
            self._log.error("Database error while fetching stories", error=e, operation="find_all", table="stories")
            raise

    async def find_by_project_id(
        self,
        project_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[StoryEntity]:
        """
        Find all stories for a specific project.

        Args:
            project_id: Project UUID
            limit: Maximum number of results (default 20)
            offset: Number of results to skip (default 0)

        Returns:
            List of StoryEntity objects
        """
        return await self.find_all(limit=limit, offset=offset, project_id=project_id)

    async def find_by_assigned_user(self, user_id: UUID) -> list[StoryEntity]:
        """
        Find all stories assigned to a specific user.

        Args:
            user_id: User UUID

        Returns:
            List of StoryEntity objects
        """
        return await self.find_all(assigned_to=user_id)

    async def save(self, story: StoryEntity) -> StoryEntity:
        """
        Save or update a story.

        Args:
            story: StoryEntity to save

        Returns:
            Saved StoryEntity if successful

        Raises:
            SQLAlchemyError: If database error occurs
        """
        start = time.time()
        try:
            # Check if story exists
            stmt = select(StoryModel).where(StoryModel.id == story.id.value)
            result = await self._session.execute(stmt)
            existing_model = result.scalar_one_or_none()

            # Convert entity to model (update existing or create new)
            model = StoryMapper.to_model(story, existing_model)
            is_insert = not existing_model

            if not existing_model:
                self._session.add(model)

            await self._session.commit()
            await self._session.refresh(model)

            duration = (time.time() - start) * 1000
            self._log.operation(
                "db.insert" if is_insert else "db.update",
                success=True,
                duration_ms=duration,
                table="stories",
                entity_id=str(story.id.value),
            )
            return StoryMapper.to_entity(model)

        except OperationalError as e:
            await self._session.rollback()
            self._log.connection_error("database", error=e, operation="save", table="stories")
            raise
        except SQLAlchemyError as e:
            await self._session.rollback()
            self._log.error(
                f"Database error while saving story {story.id.value}", error=e, operation="save", table="stories"
            )
            raise

    async def delete(self, story_id: UUID) -> bool:
        """
        Delete a story by ID.

        Args:
            story_id: Story UUID

        Returns:
            True if deleted, False if not found

        Raises:
            SQLAlchemyError: If database error occurs
        """
        start = time.time()
        try:
            stmt = select(StoryModel).where(StoryModel.id == story_id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if not model:
                return False

            await self._session.delete(model)
            await self._session.commit()

            duration = (time.time() - start) * 1000
            self._log.operation(
                "db.delete", success=True, duration_ms=duration, table="stories", entity_id=str(story_id)
            )
            return True

        except OperationalError as e:
            await self._session.rollback()
            self._log.connection_error("database", error=e, operation="delete", table="stories")
            raise
        except SQLAlchemyError as e:
            await self._session.rollback()
            self._log.error(
                f"Database error while deleting story {story_id}", error=e, operation="delete", table="stories"
            )
            raise

    async def exists(self, story_id: UUID) -> bool:
        """
        Check if a story exists by ID.

        Args:
            story_id: Story UUID

        Returns:
            True if story exists, False otherwise

        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(func.count(StoryModel.id)).where(StoryModel.id == story_id)
            result = await self._session.execute(stmt)

            return bool(int(result.scalar_one()))

        except OperationalError as e:
            self._log.connection_error("database", error=e, operation="exists", table="stories")
            raise
        except SQLAlchemyError as e:
            self._log.error(
                f"Database error while checking story existence {story_id}",
                error=e,
                operation="exists",
                table="stories",
            )
            raise

    async def update(self, story: StoryEntity) -> StoryEntity | None:
        """
        Update an existing story.

        Args:
            story: StoryEntity to update

        Returns:
            Updated StoryEntity if successful, None if not found

        Raises:
            SQLAlchemyError: If database error occurs
        """
        start = time.time()
        try:
            # Check if story exists
            stmt = select(StoryModel).where(StoryModel.id == story.id.value)
            result = await self._session.execute(stmt)
            existing_model = result.scalar_one_or_none()

            if not existing_model:
                self._log.warning(
                    "Story not found for update", entity_id=str(story.id.value), operation="update", table="stories"
                )
                return None

            # Convert entity to model (update existing)
            model = StoryMapper.to_model(story, existing_model)

            await self._session.commit()
            await self._session.refresh(model)

            duration = (time.time() - start) * 1000
            self._log.operation(
                "db.update", success=True, duration_ms=duration, table="stories", entity_id=str(story.id.value)
            )
            return StoryMapper.to_entity(model)

        except OperationalError as e:
            await self._session.rollback()
            self._log.connection_error("database", error=e, operation="update", table="stories")
            raise
        except SQLAlchemyError as e:
            await self._session.rollback()
            self._log.error(
                f"Database error while updating story {story.id.value}", error=e, operation="update", table="stories"
            )
            raise

    async def count(
        self,
        project_id: UUID | None = None,
        status: str | None = None,
        priority: str | None = None,
        assigned_to: UUID | None = None,
    ) -> int:
        """
        Count stories with optional filters.

        Args:
            project_id: Optional project filter
            status: Optional status filter
            priority: Optional priority filter
            assigned_to: Optional assigned user filter

        Returns:
            Number of stories matching filters

        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(func.count(StoryModel.id))

            if project_id:
                stmt = stmt.where(StoryModel.project_id == project_id)
            if status:
                stmt = stmt.where(StoryModel.status == status)
            if priority:
                stmt = stmt.where(StoryModel.priority == priority)
            if assigned_to:
                stmt = stmt.where(StoryModel.assigned_to == assigned_to)

            result = await self._session.execute(stmt)
            return int(result.scalar_one())

        except OperationalError as e:
            self._log.connection_error("database", error=e, operation="count", table="stories")
            raise
        except SQLAlchemyError as e:
            self._log.error("Database error while counting stories", error=e, operation="count", table="stories")
            raise
