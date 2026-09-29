"""Get dashboard statistics use case."""

from src.app.features.dashboard.application.dtos.dashboard_dto import DashboardStatsResponse
from src.app.features.dashboard.application.mappers.dashboard_mapper import (
    to_dashboard_stats_response,
    to_project_summary,
    to_story_summary,
)
from src.app.features.dashboard.domain.repositories.dashboard_repository import DashboardRepository
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.application.request_context import RequestContext
from src.app.shared.logging import get_logger, set_user_id


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

    async def execute(self, ctx: RequestContext) -> DashboardStatsResponse:
        """
        Execute get dashboard stats use case.

        Uses a single aggregated query for counts and separate queries
        for recent items lists.

        Args:
            ctx: Caller identity and workspace; every count is confined to the workspace

        Returns:
            DashboardStatsResponse with statistics
        """
        log = get_logger(__name__)
        user_id = str(ctx.user_id)
        set_user_id(user_id)
        workspace_id = ctx.workspace_id.value

        log.debug(
            "Fetching dashboard statistics",
            extra={"event_type": "dashboard.stats.fetch_started", "user_id": user_id},
        )

        # Aggregate query optimization: fetch all counts in single database roundtrip
        stats = await self._dashboard_repo.get_aggregated_stats(workspace_id=workspace_id, user_id=ctx.user_id.value)

        recent_projects_raw = await self._project_repo.find_all(workspace_id=workspace_id, limit=5)
        recent_projects = [to_project_summary(p) for p, _ in recent_projects_raw]

        recent_stories_raw = await self._story_repo.find_all(workspace_id=workspace_id, limit=5)
        recent_stories = [to_story_summary(s) for s in recent_stories_raw]

        log.info(
            "Dashboard statistics retrieved",
            extra={
                "event_type": "dashboard.stats.retrieved",
                "total_projects": stats["total_projects"],
                "active_projects": stats["active_projects"],
                "total_stories": stats["total_stories"],
                "assigned_stories": stats["assigned_stories"],
                "completed_stories": stats["completed_stories"],
                "recent_projects_count": len(recent_projects),
                "recent_stories_count": len(recent_stories),
            },
        )

        return to_dashboard_stats_response(stats, recent_projects, recent_stories)
