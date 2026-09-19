"""Project repository implementation using SQLAlchemy."""

import time
from datetime import datetime
from uuid import UUID

from sqlalchemy import case, func, or_, select
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
from src.app.shared.logging import get_logger


def _apply_project_filters(
    stmt,
    status: str | None = None,
    client_id: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    updated_from: datetime | None = None,
    updated_to: datetime | None = None,
    search: str | None = None,
):
    """Apply common filter conditions to a project query statement."""
    if status:
        stmt = stmt.where(ProjectModel.status == status)
    if client_id:
        stmt = stmt.where(ProjectModel.client_id == client_id)
    if created_from:
        stmt = stmt.where(ProjectModel.created_at >= created_from)
    if created_to:
        stmt = stmt.where(ProjectModel.created_at <= created_to)
    if updated_from:
        stmt = stmt.where(ProjectModel.updated_at >= updated_from)
    if updated_to:
        stmt = stmt.where(ProjectModel.updated_at <= updated_to)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(ProjectModel.name.ilike(pattern), ProjectModel.code.ilike(pattern)))
    return stmt


class ProjectRepositoryImpl(ProjectRepository):
    """SQLAlchemy implementation of ProjectRepository."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session
        self._log = get_logger(__name__)

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

        except OperationalError:
            self._log.exception("Database connection error", extra={"operation": "find_by_id", "table": "projects"})
            raise
        except SQLAlchemyError:
            self._log.exception(
                "Database error while fetching project", extra={"operation": "find_by_id", "table": "projects"}
            )
            raise

    async def find_all(
        self,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
        client_id: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        updated_from: datetime | None = None,
        updated_to: datetime | None = None,
        search: str | None = None,
    ) -> list[tuple[ProjectEntity, str]]:
        """
        Find all projects with pagination and optional filtering.

        Args:
            limit: Maximum number of results (default 20)
            offset: Number of results to skip (default 0)
            status: Optional status filter (active, completed, archived)
            client_id: Optional client UUID filter
            created_from: Optional lower bound on created_at
            created_to: Optional upper bound on created_at
            updated_from: Optional lower bound on updated_at
            updated_to: Optional upper bound on updated_at
            search: Optional substring match on name or code (case-insensitive)

        Returns:
            List of tuples (ProjectEntity, client_name)

        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(ProjectModel, ClientModel.name).join(ClientModel, ProjectModel.client_id == ClientModel.id)

            stmt = _apply_project_filters(
                stmt,
                status=status,
                client_id=client_id,
                created_from=created_from,
                created_to=created_to,
                updated_from=updated_from,
                updated_to=updated_to,
                search=search,
            )

            stmt = stmt.order_by(ProjectModel.created_at.desc())
            stmt = stmt.limit(limit).offset(offset)

            result = await self._session.execute(stmt)
            rows = result.all()

            return [(ProjectMapper.to_entity(model), client_name) for model, client_name in rows]

        except OperationalError:
            self._log.exception("Database connection error", extra={"operation": "find_all", "table": "projects"})
            raise
        except SQLAlchemyError:
            self._log.exception(
                "Database error while fetching projects", extra={"operation": "find_all", "table": "projects"}
            )
            raise

    async def save(self, project: ProjectEntity) -> ProjectEntity:
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
            self._log.info(
                "Database operation completed",
                extra={
                    "event_type": "db.insert" if is_insert else "db.update",
                    "success": True,
                    "duration_ms": duration,
                    "table": "projects",
                    "entity_id": str(project.id.value),
                },
            )
            return ProjectMapper.to_entity(model)

        except OperationalError:
            await self._session.rollback()
            self._log.exception("Database connection error", extra={"operation": "save", "table": "projects"})
            raise
        except SQLAlchemyError:
            await self._session.rollback()
            self._log.exception("Database error while saving project", extra={"operation": "save", "table": "projects"})
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
            self._log.info(
                "Database operation completed",
                extra={
                    "event_type": "db.delete",
                    "success": True,
                    "duration_ms": duration,
                    "table": "projects",
                    "entity_id": str(project_id),
                },
            )
            return True

        except OperationalError:
            await self._session.rollback()
            self._log.exception("Database connection error", extra={"operation": "delete", "table": "projects"})
            raise
        except SQLAlchemyError:
            await self._session.rollback()
            self._log.exception(
                "Database error while deleting project", extra={"operation": "delete", "table": "projects"}
            )
            raise

    async def count(
        self,
        status: str | None = None,
        client_id: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        updated_from: datetime | None = None,
        updated_to: datetime | None = None,
        search: str | None = None,
    ) -> int:
        """
        Count projects with optional filters.

        Args:
            status: Optional status filter
            client_id: Optional client UUID filter
            created_from: Optional lower bound on created_at
            created_to: Optional upper bound on created_at
            updated_from: Optional lower bound on updated_at
            updated_to: Optional upper bound on updated_at
            search: Optional substring match on name or code (case-insensitive)

        Returns:
            Number of projects

        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(func.count(ProjectModel.id))

            stmt = _apply_project_filters(
                stmt,
                status=status,
                client_id=client_id,
                created_from=created_from,
                created_to=created_to,
                updated_from=updated_from,
                updated_to=updated_to,
                search=search,
            )

            result = await self._session.execute(stmt)
            return int(result.scalar_one())

        except OperationalError:
            self._log.exception("Database connection error", extra={"operation": "count", "table": "projects"})
            raise
        except SQLAlchemyError:
            self._log.exception(
                "Database error while counting projects", extra={"operation": "count", "table": "projects"}
            )
            raise

    async def exists(self, project_id: UUID) -> bool:
        """
        Check if a project exists by ID.

        Args:
            project_id: Project UUID

        Returns:
            True if the project exists, False otherwise

        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(ProjectModel.id).where(ProjectModel.id == project_id).limit(1)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None

        except OperationalError:
            self._log.exception("Database connection error", extra={"operation": "exists", "table": "projects"})
            raise
        except SQLAlchemyError:
            self._log.exception(
                "Database error while checking project existence",
                extra={"operation": "exists", "table": "projects"},
            )
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

        except OperationalError:
            self._log.exception(
                "Database connection error", extra={"operation": "get_story_counts", "table": "stories"}
            )
            raise
        except SQLAlchemyError:
            self._log.exception(
                "Database error while fetching story counts",
                extra={"operation": "get_story_counts", "table": "stories"},
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

        except OperationalError:
            self._log.exception(
                "Database connection error", extra={"operation": "get_story_counts_batch", "table": "stories"}
            )
            raise
        except SQLAlchemyError:
            self._log.exception(
                "Database error while fetching batch story counts",
                extra={"operation": "get_story_counts_batch", "table": "stories"},
            )
            raise

    async def count_active_by_user(self, user_id: UUID) -> int:
        """
        Count active projects owned by a specific user.

        Args:
            user_id: User UUID

        Returns:
            Number of active projects for the user
        """
        try:
            stmt = (
                select(func.count(ProjectModel.id))
                .where(ProjectModel.created_by == user_id)
                .where(ProjectModel.status == "active")
            )
            result = await self._session.execute(stmt)
            return int(result.scalar_one())

        except OperationalError:
            self._log.exception(
                "Database connection error", extra={"operation": "count_active_by_user", "table": "projects"}
            )
            raise
        except SQLAlchemyError:
            self._log.exception(
                "Database error counting active projects by user",
                extra={"operation": "count_active_by_user", "table": "projects"},
            )
            raise

    async def has_active_projects_for_client(self, client_id: UUID) -> bool:
        """
        Check whether a client has any active projects.

        Args:
            client_id: Client UUID

        Returns:
            True if at least one active project exists for this client
        """
        try:
            stmt = (
                select(ProjectModel.id)
                .where(ProjectModel.client_id == client_id)
                .where(ProjectModel.status == "active")
                .limit(1)
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None

        except OperationalError:
            self._log.exception(
                "Database connection error",
                extra={"operation": "has_active_projects_for_client", "table": "projects"},
            )
            raise
        except SQLAlchemyError:
            self._log.exception(
                "Database error checking active projects for client",
                extra={"operation": "has_active_projects_for_client", "table": "projects"},
            )
            raise

    async def delete_archived_by_client(self, client_id: UUID) -> int:
        """
        Delete all archived projects for a client (cascade removes stories).

        Args:
            client_id: Client UUID

        Returns:
            Number of projects deleted
        """
        start = time.time()
        try:
            stmt = select(ProjectModel).where(
                ProjectModel.client_id == client_id,
                ProjectModel.status == "archived",
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            count = 0
            for model in models:
                await self._session.delete(model)
                count += 1

            if count > 0:
                await self._session.commit()

            duration = (time.time() - start) * 1000
            self._log.info(
                "Archived projects deleted for client",
                extra={
                    "event_type": "projects.archived.deleted_by_client",
                    "client_id": str(client_id),
                    "count": count,
                    "duration_ms": duration,
                },
            )
            return count

        except OperationalError:
            await self._session.rollback()
            self._log.exception(
                "Database connection error",
                extra={"operation": "delete_archived_by_client", "table": "projects"},
            )
            raise
        except SQLAlchemyError:
            await self._session.rollback()
            self._log.exception(
                "Database error deleting archived projects for client",
                extra={"operation": "delete_archived_by_client", "table": "projects"},
            )
            raise
