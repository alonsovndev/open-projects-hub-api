"""Project repository implementation using SQLAlchemy."""

import time
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.clients.infrastructure.models.client_model import ClientModel
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.projects.infrastructure.mappers.project_mapper import ProjectMapper
from src.app.features.projects.infrastructure.models.project_model import ProjectModel
from src.app.features.stories.domain.value_objects.story_status import StoryStatus

# Cross-feature query for performance optimization (see ADR-001)
from src.app.features.stories.infrastructure.models.story_model import StoryModel
from src.app.shared.logging import TechnicalLogger, get_logger


class ProjectRepositoryImpl(ProjectRepository):
    """SQLAlchemy implementation of ProjectRepository."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session
        self._log = TechnicalLogger(get_logger(__name__), component="database")

    async def find_by_id(self, project_id: UUID) -> tuple[ProjectEntity, str] | None:
        """
        Find project by ID with client name.

        Args:
            project_id: Project UUID

        Returns:
            Tuple of (ProjectEntity, client_name) if found, None otherwise

        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = (
                select(ProjectModel, ClientModel.name)
                .join(ClientModel, ProjectModel.client_id == ClientModel.id)
                .where(ProjectModel.id == project_id)
            )
            result = await self._session.execute(stmt)
            row = result.one_or_none()

            if row:
                project_model, client_name = row
                return (ProjectMapper.to_entity(project_model), client_name)

            return None

        except OperationalError as e:
            self._log.connection_error("postgresql", error=e, operation="find_by_id", table="projects")
            raise
        except SQLAlchemyError as e:
            self._log.error(
                f"Database error while fetching project {project_id}", error=e, operation="find_by_id", table="projects"
            )
            raise

    async def find_all(
        self,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
    ) -> list[tuple[ProjectEntity, str]]:
        """
        Find all projects with pagination and optional filtering.

        Args:
            limit: Maximum number of results (default 20)
            offset: Number of results to skip (default 0)
            status: Optional status filter (active, completed, archived)

        Returns:
            List of tuples (ProjectEntity, client_name)

        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(ProjectModel, ClientModel.name).join(ClientModel, ProjectModel.client_id == ClientModel.id)

            if status:
                stmt = stmt.where(ProjectModel.status == status)

            stmt = stmt.order_by(ProjectModel.created_at.desc())
            stmt = stmt.limit(limit).offset(offset)

            result = await self._session.execute(stmt)
            rows = result.all()

            return [(ProjectMapper.to_entity(model), client_name) for model, client_name in rows]

        except OperationalError as e:
            self._log.connection_error("postgresql", error=e, operation="find_all", table="projects")
            raise
        except SQLAlchemyError as e:
            self._log.error("Database error while fetching projects", error=e, operation="find_all", table="projects")
            raise

    async def save(self, project: ProjectEntity) -> ProjectEntity | None:
        """
        Save or update a project.

        Args:
            project: ProjectEntity to save

        Returns:
            Saved ProjectEntity if successful

        Raises:
            SQLAlchemyError: If database error occurs
        """
        start = time.time()
        try:
            stmt = select(ProjectModel).where(ProjectModel.id == project.id.value)
            result = await self._session.execute(stmt)
            existing_model = result.scalar_one_or_none()

            model = ProjectMapper.to_model(project, existing_model)
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
                table="projects",
                entity_id=str(project.id.value),
            )
            return ProjectMapper.to_entity(model)

        except OperationalError as e:
            await self._session.rollback()
            self._log.connection_error("postgresql", error=e, operation="save", table="projects")
            raise
        except SQLAlchemyError as e:
            await self._session.rollback()
            self._log.error(
                f"Database error while saving project {project.id.value}", error=e, operation="save", table="projects"
            )
            raise

    async def delete(self, project_id: UUID) -> bool:
        """
        Delete a project by ID.

        Args:
            project_id: Project UUID

        Returns:
            True if deleted, False if not found

        Raises:
            SQLAlchemyError: If database error occurs
        """
        start = time.time()
        try:
            stmt = select(ProjectModel).where(ProjectModel.id == project_id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if not model:
                return False

            await self._session.delete(model)
            await self._session.commit()

            duration = (time.time() - start) * 1000
            self._log.operation(
                "db.delete", success=True, duration_ms=duration, table="projects", entity_id=str(project_id)
            )
            return True

        except OperationalError as e:
            await self._session.rollback()
            self._log.connection_error("postgresql", error=e, operation="delete", table="projects")
            raise
        except SQLAlchemyError as e:
            await self._session.rollback()
            self._log.error(
                f"Database error while deleting project {project_id}", error=e, operation="delete", table="projects"
            )
            raise

    async def count(self, status: str | None = None) -> int:
        """
        Count projects with optional status filter.

        Args:
            status: Optional status filter

        Returns:
            Number of projects

        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(func.count(ProjectModel.id))

            if status:
                stmt = stmt.where(ProjectModel.status == status)

            result = await self._session.execute(stmt)
            return int(result.scalar_one())

        except OperationalError as e:
            self._log.connection_error("postgresql", error=e, operation="count", table="projects")
            raise
        except SQLAlchemyError as e:
            self._log.error("Database error while counting projects", error=e, operation="count", table="projects")
            raise

    async def get_story_counts(self, project_id: UUID) -> tuple[int, int]:
        """
        Get total and completed story counts for a project.

        NOTE: Cross-feature query optimization (see ADR-001)
        This method queries the stories table directly for performance.
        Trade-off: Better query performance vs. feature coupling.
        Acceptable for monolithic deployment model.

        Args:
            project_id: Project UUID

        Returns:
            Tuple of (total_stories, completed_stories)

        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(
                func.count(StoryModel.id).label("total"),
                func.sum(case((StoryModel.status == StoryStatus.DONE.value, 1), else_=0)).label("completed"),
            ).where(StoryModel.project_id == project_id)

            result = await self._session.execute(stmt)
            row = result.one()

            total = row.total or 0
            completed = row.completed or 0

            return (total, completed)

        except OperationalError as e:
            self._log.connection_error("postgresql", error=e, operation="get_story_counts", table="stories")
            raise
        except SQLAlchemyError as e:
            self._log.error(
                f"Database error while fetching story counts for project {project_id}",
                error=e,
                operation="get_story_counts",
                table="stories",
            )
            raise

    async def get_story_counts_batch(self, project_ids: list[UUID]) -> dict[UUID, tuple[int, int]]:
        """
        Get story counts for multiple projects in a single query.

        NOTE: Cross-feature query optimization (see ADR-001)
        This method queries the stories table directly for performance.
        Trade-off: Better query performance vs. feature coupling.
        Acceptable for monolithic deployment model.

        Args:
            project_ids: List of project UUIDs

        Returns:
            Dict mapping project_id to (total_stories, completed_stories)

        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = (
                select(
                    StoryModel.project_id,
                    func.count(StoryModel.id).label("total"),
                    func.sum(case((StoryModel.status == StoryStatus.DONE.value, 1), else_=0)).label("completed"),
                )
                .where(StoryModel.project_id.in_(project_ids))
                .group_by(StoryModel.project_id)
            )

            result = await self._session.execute(stmt)
            rows = result.all()

            # Pre-populate with zeros to ensure all requested projects have entries
            counts = dict.fromkeys(project_ids, (0, 0))

            for row in rows:
                total = row.total or 0
                completed = row.completed or 0
                counts[row.project_id] = (total, completed)

            return counts

        except OperationalError as e:
            self._log.connection_error("postgresql", error=e, operation="get_story_counts_batch", table="stories")
            raise
        except SQLAlchemyError as e:
            self._log.error(
                "Database error while fetching batch story counts",
                error=e,
                operation="get_story_counts_batch",
                table="stories",
            )
            raise
