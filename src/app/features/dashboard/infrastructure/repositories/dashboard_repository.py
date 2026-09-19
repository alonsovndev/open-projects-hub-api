"""Dashboard repository for optimized aggregated queries."""

from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.dashboard.domain.repositories.dashboard_repository import DashboardRepository
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.features.projects.infrastructure.models.project_model import ProjectModel
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.features.stories.infrastructure.models.story_model import StoryModel
from src.app.shared.logging import get_logger


class DashboardRepositoryImpl(DashboardRepository):
    """SQLAlchemy implementation of DashboardRepository."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository.

        Args:
            session: Database session
        """
        self._session = session
        self._log = get_logger(__name__)

    async def get_aggregated_stats(self, user_id: UUID | None = None) -> dict:
        """
        Get all dashboard count statistics in a single query.

        Uses subqueries to aggregate counts from both projects and stories tables.

        Args:
            user_id: Optional user ID for user-specific stats

        Returns:
            Dictionary with all dashboard count statistics

        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            # Project counts subquery
            project_stats = (
                select(
                    func.count(ProjectModel.id).label("total_projects"),
                    func.sum(case((ProjectModel.status == ProjectStatus.ACTIVE, 1), else_=0)).label("active_projects"),
                )
                .select_from(ProjectModel)
                .subquery()
            )

            # Story counts subquery
            story_counts_cols = [
                func.count(StoryModel.id).label("total_stories"),
                func.sum(case((StoryModel.status == StoryStatus.DONE, 1), else_=0)).label("completed_stories"),
            ]

            if user_id:
                story_counts_cols.append(
                    func.sum(case((StoryModel.assigned_to == user_id, 1), else_=0)).label("assigned_stories")
                )

            story_stats = select(*story_counts_cols).select_from(StoryModel).subquery()

            # Combine both subqueries in a single SELECT
            stmt = select(
                project_stats.c.total_projects,
                project_stats.c.active_projects,
                story_stats.c.total_stories,
                story_stats.c.completed_stories,
            )

            if user_id:
                stmt = stmt.add_columns(story_stats.c.assigned_stories)

            stmt = stmt.select_from(project_stats).select_from(story_stats)

            result = await self._session.execute(stmt)
            row = result.one()

            stats = {
                "total_projects": row.total_projects or 0,
                "active_projects": row.active_projects or 0,
                "total_stories": row.total_stories or 0,
                "completed_stories": row.completed_stories or 0,
                "assigned_stories": (row.assigned_stories if user_id else 0) or 0,
            }

            self._log.debug(
                "Dashboard aggregated stats query completed",
                extra={
                    "user_id": str(user_id) if user_id else None,
                    "total_projects": stats["total_projects"],
                    "total_stories": stats["total_stories"],
                },
            )

            return stats

        except OperationalError:
            self._log.exception(
                "Database connection error",
                extra={"operation": "get_aggregated_stats", "table": "projects,stories"},
            )
            raise
        except SQLAlchemyError:
            self._log.exception(
                "Failed to retrieve aggregated dashboard statistics",
                extra={
                    "operation": "get_aggregated_stats",
                    "user_id": str(user_id) if user_id else None,
                },
            )
            raise
