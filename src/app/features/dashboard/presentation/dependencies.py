"""Dependency injection for dashboard feature."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.dashboard.application.use_cases.get_dashboard_stats import GetDashboardStatsUseCase
from src.app.features.dashboard.infrastructure.repositories.dashboard_repository import DashboardRepository
from src.app.features.projects.infrastructure.repositories.project_repository_impl import ProjectRepositoryImpl
from src.app.features.stories.infrastructure.repositories.story_repository_impl import StoryRepositoryImpl
from src.app.shared.presentation.dependencies import get_database_session


async def get_dashboard_repository(
    session: AsyncSession = Depends(get_database_session),
) -> DashboardRepository:
    """Get dashboard repository instance."""
    return DashboardRepository(session)


async def get_project_repository(
    session: AsyncSession = Depends(get_database_session),
) -> ProjectRepositoryImpl:
    """Get project repository instance."""
    return ProjectRepositoryImpl(session)


async def get_story_repository(
    session: AsyncSession = Depends(get_database_session),
) -> StoryRepositoryImpl:
    """Get story repository instance."""
    return StoryRepositoryImpl(session)


async def get_get_dashboard_stats_use_case(
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repository),
    project_repo: ProjectRepositoryImpl = Depends(get_project_repository),
    story_repo: StoryRepositoryImpl = Depends(get_story_repository),
) -> GetDashboardStatsUseCase:
    """Get GetDashboardStatsUseCase instance."""
    return GetDashboardStatsUseCase(dashboard_repo, project_repo, story_repo)