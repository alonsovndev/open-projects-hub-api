"""
Dashboard feature dependency composition.

All dependency wiring for dashboard statistics use cases.

Dependencies:
- Infrastructure: Database session
- Repositories: Multiple repositories (dashboard, project, story)

Use Cases:
- Get Dashboard Stats: Aggregate statistics for user dashboard view
  (project counts, story counts, completion metrics)

Data Access:
Read-only feature. Uses direct SQL queries for performance-optimized
aggregate calculations. No write operations.

Usage:
    from src.app.composition import get_dashboard_stats_use_case

    @router.get("/stats")
    async def get_stats(
        use_case: GetDashboardStatsUseCase = Depends(get_dashboard_stats_use_case),
    ):
        return await use_case.execute(...)
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.composition.infrastructure import get_database_session
from src.app.composition.repositories import get_story_repository
from src.app.features.dashboard.application.use_cases.get_dashboard_stats import GetDashboardStatsUseCase
from src.app.features.dashboard.infrastructure.repositories.dashboard_repository import DashboardRepository
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.stories.domain.repositories.story_repository import StoryRepository


# Feature-specific repositories
async def get_dashboard_repository(
    session: AsyncSession = Depends(get_database_session),
) -> DashboardRepository:
    """Dashboard repository factory (feature-specific)."""
    return DashboardRepository(session)


async def get_project_repository(
    session: AsyncSession = Depends(get_database_session),
) -> ProjectRepository:
    """
    Project repository factory (feature-specific for dashboard).

    Note: Projects feature has its own project repository factory.
    This is duplicated here because dashboard queries projects differently
    (read-only aggregate queries vs full CRUD).
    """
    from src.app.features.projects.infrastructure.repositories.project_repository_impl import ProjectRepositoryImpl

    return ProjectRepositoryImpl(session)


# Use case factories
async def get_dashboard_stats_use_case(
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repository),
    project_repo: ProjectRepository = Depends(get_project_repository),
    story_repo: StoryRepository = Depends(get_story_repository),
) -> GetDashboardStatsUseCase:
    """
    GetDashboardStatsUseCase factory.

    Depends on multiple repositories for aggregated dashboard data.
    """
    return GetDashboardStatsUseCase(dashboard_repo, project_repo, story_repo)
