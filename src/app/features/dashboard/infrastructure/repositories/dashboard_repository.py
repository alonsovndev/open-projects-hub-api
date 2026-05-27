"""
Dashboard repository for optimized aggregated queries.

Provides single aggregated queries for dashboard statistics to minimize database round trips.
"""

from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.projects.infrastructure.models.project_model import ProjectModel
from src.app.features.stories.infrastructure.models.story_model import StoryModel
from src.app.shared.logging import get_logger, log_error_event


log = get_logger(__name__)


class DashboardRepository:
    """Repository for dashboard-specific queries."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository.

        Args:
            session: Database session
        """
        self._session = session

    async def get_aggregated_stats(self, user_id: UUID | None = None) -> dict:
        """
        Get all dashboard count statistics in a single query.

        Uses subqueries to aggregate counts from both projects and stories tables.

        Args:
            user_id: Optional user ID for user-specific stats

        Returns:
            Dictionary with all dashboard count statistics:
            - total_projects: int
            - active_projects: int
            - total_stories: int
            - assigned_stories: int (if user_id provided, otherwise 0)
            - completed_stories: int
        """
        try:
            # Project counts subquery
            project_stats = (
                select(
                    func.count(ProjectModel.id).label("total_projects"),
                    func.sum(case((ProjectModel.status == "active", 1), else_=0)).label("active_projects"),
                )
                .select_from(ProjectModel)
                .subquery()
            )

            # Story counts subquery
            story_counts_cols = [
                func.count(StoryModel.id).label("total_stories"),
                func.sum(case((StoryModel.status == "done", 1), else_=0)).label("completed_stories"),
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

            log.debug(
                "Dashboard aggregated stats query completed",
                extra={
                    "user_id": str(user_id) if user_id else None,
                    "total_projects": stats["total_projects"],
                    "total_stories": stats["total_stories"],
                },
            )

            return stats

        except Exception as e:
            log_error_event(
                logger=log,
                error_type="dashboard.database.aggregation_failed",
                message="Failed to retrieve aggregated dashboard statistics",
                error=e,
                user_id=str(user_id) if user_id else None,
            )
            raise
