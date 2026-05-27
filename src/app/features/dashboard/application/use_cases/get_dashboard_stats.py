"""Get dashboard statistics use case."""

from uuid import UUID

from src.app.features.dashboard.application.dtos.dashboard_dto import (
    DashboardStatsResponse,
    ProjectSummary,
    StorySummary,
)
from src.app.features.dashboard.infrastructure.repositories.dashboard_repository import DashboardRepository
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.logging import get_logger, log_business_event, log_error_event


log = get_logger(__name__)


class GetDashboardStatsUseCase:
    """Use case for getting dashboard statistics."""

    def __init__(
        self,
        dashboard_repository: DashboardRepository,
        project_repository: ProjectRepository,
        story_repository: StoryRepository,
    ):
        """
        Initialize use case.

        Args:
            dashboard_repository: Dashboard repository for aggregated stats
            project_repository: Project repository for recent projects
            story_repository: Story repository for recent stories
        """
        self._dashboard_repo = dashboard_repository
        self._project_repo = project_repository
        self._story_repo = story_repository

    async def execute(self, user_id: str) -> DashboardStatsResponse:
        """
        Execute get dashboard stats use case.

        Uses a single aggregated query for counts and separate queries
        for recent items lists.

        Args:
            user_id: Current user ID

        Returns:
            DashboardStatsResponse with statistics
        """
        try:
            user_uuid = UUID(user_id)

            log.debug(
                "Fetching dashboard statistics",
                extra={
                    "user_id": user_id,
                    "event_type": "dashboard.stats.fetch_started",
                },
            )

            # Aggregate query optimization: fetch all counts in single database roundtrip
            stats = await self._dashboard_repo.get_aggregated_stats(user_uuid)

            recent_projects_raw = await self._project_repo.find_all(limit=5)
            recent_projects = [
                ProjectSummary(
                    id=str(p.id.value),
                    name=p.name,
                    status=p.status.value,
                    created_at=p.created_at.isoformat(),
                )
                for p, client_name in recent_projects_raw
            ]

            recent_stories_raw = await self._story_repo.find_all(limit=5)
            recent_stories = [
                StorySummary(
                    id=str(s.id.value),
                    title=s.title,
                    status=s.status.value,
                    priority=s.priority.value,
                    created_at=s.created_at.isoformat(),
                )
                for s in recent_stories_raw
            ]

            log_business_event(
                logger=log,
                event_type="dashboard.stats.retrieved",
                message="Dashboard statistics retrieved successfully",
                user_id=user_id,
                additional_data={
                    "total_projects": stats["total_projects"],
                    "active_projects": stats["active_projects"],
                    "total_stories": stats["total_stories"],
                    "assigned_stories": stats["assigned_stories"],
                    "completed_stories": stats["completed_stories"],
                    "recent_projects_count": len(recent_projects),
                    "recent_stories_count": len(recent_stories),
                },
            )

            return DashboardStatsResponse(
                total_projects=stats["total_projects"],
                active_projects=stats["active_projects"],
                total_stories=stats["total_stories"],
                assigned_stories=stats["assigned_stories"],
                completed_stories=stats["completed_stories"],
                recent_projects=recent_projects,
                recent_stories=recent_stories,
            )

        except ValueError as e:
            log_error_event(
                logger=log,
                error_type="dashboard.stats.invalid_user_id",
                message="Invalid user ID format for dashboard stats",
                error=e,
                user_id=user_id,
            )
            raise
        except Exception as e:
            log_error_event(
                logger=log,
                error_type="dashboard.stats.unexpected_error",
                message="Unexpected error retrieving dashboard statistics",
                error=e,
                user_id=user_id,
            )
            raise
