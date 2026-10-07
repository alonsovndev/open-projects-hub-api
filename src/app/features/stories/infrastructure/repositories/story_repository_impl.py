"""Story repository implementation using SQLAlchemy."""

import time
from datetime import UTC, datetime, time as time_of_day, timedelta
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

# Stories are scoped through their project's workspace (cross-feature join, see ADR-001)
from src.app.features.projects.infrastructure.models.project_model import ProjectModel
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.queries.backlog_query import BacklogQuery
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.infrastructure.mappers.story_mapper import StoryMapper
from src.app.features.stories.infrastructure.models.story_model import StoryModel
from src.app.shared.logging import get_logger


def _in_workspace(stmt: Select, workspace_id: UUID) -> Select:
    """Confine a stories statement to one workspace via the owning project."""
    return stmt.join(ProjectModel, StoryModel.project_id == ProjectModel.id).where(
        ProjectModel.workspace_id == workspace_id
    )


class StoryRepositoryImpl(StoryRepository):
    """SQLAlchemy implementation of StoryRepository."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session
        self._log = get_logger(__name__)

    async def find_by_id(self, story_id: UUID, *, workspace_id: UUID) -> StoryEntity | None:
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
            stmt = _in_workspace(select(StoryModel), workspace_id).where(StoryModel.id == story_id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                return StoryMapper.to_entity(model)
            return None

        except OperationalError:
            self._log.exception("Database connection error", extra={"operation": "find_by_id", "table": "stories"})
            raise
        except SQLAlchemyError:
            self._log.exception(
                "Database error while fetching story", extra={"operation": "find_by_id", "table": "stories"}
            )
            raise

    async def find_all(
        self,
        *,
        workspace_id: UUID,
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
            stmt = _in_workspace(select(StoryModel), workspace_id)

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

        except OperationalError:
            self._log.exception("Database connection error", extra={"operation": "find_all", "table": "stories"})
            raise
        except SQLAlchemyError:
            self._log.exception(
                "Database error while fetching stories", extra={"operation": "find_all", "table": "stories"}
            )
            raise

    async def find_by_project_id(
        self,
        project_id: UUID,
        *,
        workspace_id: UUID,
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
        return await self.find_all(workspace_id=workspace_id, limit=limit, offset=offset, project_id=project_id)

    @staticmethod
    def _apply_backlog_scope(stmt: Select, query: BacklogQuery) -> Select:
        """Narrow a statement to a backlog scope, without ordering or pagination."""
        stmt = _in_workspace(stmt, query.workspace_id).where(StoryModel.project_id == query.project_id)

        if query.status:
            stmt = stmt.where(StoryModel.status == query.status.value)
        if query.created_from:
            stmt = stmt.where(
                StoryModel.created_at >= datetime.combine(query.created_from, time_of_day.min, tzinfo=UTC)
            )
        if query.created_to:
            # created_to is an inclusive calendar day, so compare against the start of the
            # next one rather than truncating created_at, which would not use the index.
            next_day = query.created_to + timedelta(days=1)
            stmt = stmt.where(StoryModel.created_at < datetime.combine(next_day, time_of_day.min, tzinfo=UTC))

        return stmt

    async def find_backlog(self, query: BacklogQuery) -> list[StoryEntity]:
        """
        Find a scoped slice of a project's backlog, in reading order.

        Args:
            query: The backlog scope

        Returns:
            List of StoryEntity objects ordered by priority then age

        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            # The priority column stores its enum by value, which sorts alphabetically
            # (high, low, medium) — not by importance. Rank it explicitly instead.
            #
            # Written as comparisons rather than case(value=...): the column is a PostgreSQL
            # `storypriority` enum, and the shorthand binds its whens as bare VARCHAR, which
            # Postgres refuses to compare against the enum type.
            priority_rank = case(
                (StoryModel.priority == StoryPriority.HIGH.value, 0),
                (StoryModel.priority == StoryPriority.MEDIUM.value, 1),
                (StoryModel.priority == StoryPriority.LOW.value, 2),
                else_=3,
            )

            stmt = self._apply_backlog_scope(select(StoryModel), query)
            stmt = stmt.order_by(priority_rank, StoryModel.created_at.asc())
            stmt = stmt.limit(query.limit).offset(query.offset)

            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [StoryMapper.to_entity(model) for model in models]

        except OperationalError:
            self._log.exception("Database connection error", extra={"operation": "find_backlog", "table": "stories"})
            raise
        except SQLAlchemyError:
            self._log.exception(
                "Database error while fetching backlog", extra={"operation": "find_backlog", "table": "stories"}
            )
            raise

    async def count_backlog(self, query: BacklogQuery) -> int:
        """
        Count the stories matching a backlog scope, ignoring its pagination.

        Args:
            query: The backlog scope

        Returns:
            Number of stories in scope

        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = self._apply_backlog_scope(select(func.count(StoryModel.id)), query)

            result = await self._session.execute(stmt)
            return int(result.scalar_one())

        except OperationalError:
            self._log.exception("Database connection error", extra={"operation": "count_backlog", "table": "stories"})
            raise
        except SQLAlchemyError:
            self._log.exception(
                "Database error while counting backlog", extra={"operation": "count_backlog", "table": "stories"}
            )
            raise

    async def find_by_assigned_user(self, user_id: UUID, *, workspace_id: UUID) -> list[StoryEntity]:
        """
        Find all stories assigned to a specific user.

        Args:
            user_id: User UUID

        Returns:
            List of StoryEntity objects
        """
        return await self.find_all(workspace_id=workspace_id, assigned_to=user_id)

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
            self._log.info(
                "Database operation completed",
                extra={
                    "event_type": "db.insert" if is_insert else "db.update",
                    "success": True,
                    "duration_ms": duration,
                    "table": "stories",
                    "entity_id": str(story.id.value),
                },
            )
            return StoryMapper.to_entity(model)

        except OperationalError:
            await self._session.rollback()
            self._log.exception("Database connection error", extra={"operation": "save", "table": "stories"})
            raise
        except SQLAlchemyError:
            await self._session.rollback()
            self._log.exception("Database error while saving story", extra={"operation": "save", "table": "stories"})
            raise

    async def delete(self, story_id: UUID, *, workspace_id: UUID) -> bool:
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
            stmt = _in_workspace(select(StoryModel), workspace_id).where(StoryModel.id == story_id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if not model:
                return False

            await self._session.delete(model)
            await self._session.commit()

            duration = (time.time() - start) * 1000
            self._log.info(
                "Database operation completed",
                extra={
                    "event_type": "db.delete",
                    "success": True,
                    "duration_ms": duration,
                    "table": "stories",
                    "entity_id": str(story_id),
                },
            )
            return True

        except OperationalError:
            await self._session.rollback()
            self._log.exception("Database connection error", extra={"operation": "delete", "table": "stories"})
            raise
        except SQLAlchemyError:
            await self._session.rollback()
            self._log.exception(
                "Database error while deleting story", extra={"operation": "delete", "table": "stories"}
            )
            raise

    async def count(
        self,
        *,
        workspace_id: UUID,
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
            stmt = _in_workspace(select(func.count(StoryModel.id)), workspace_id)

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

        except OperationalError:
            self._log.exception("Database connection error", extra={"operation": "count", "table": "stories"})
            raise
        except SQLAlchemyError:
            self._log.exception(
                "Database error while counting stories", extra={"operation": "count", "table": "stories"}
            )
            raise
