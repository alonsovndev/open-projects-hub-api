"""Dependency injection for dashboard feature."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.dashboard.application.use_cases.get_dashboard_stats import GetDashboardStatsUseCase
from src.app.features.dashboard.infrastructure.repositories.dashboard_repository import DashboardRepository
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.projects.infrastructure.repositories.project_repository_impl import ProjectRepositoryImpl
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.stories.infrastructure.repositories.story_repository_impl import StoryRepositoryImpl
from src.app.shared.presentation.dependencies import get_database_session


async def get_dashboard_repository(
    session: AsyncSession = Depends(get_database_session),
) -> DashboardRepository:
    """Get dashboard repository instance."""
    return DashboardRepository(session)


async def get_project_repository(
    session: AsyncSession = Depends(get_database_session),
) -> ProjectRepository:
    """
    Get project repository instance.
    
    Args:
        session: Database session
        
    Returns:
        ProjectRepository interface
    """
    return ProjectRepositoryImpl(session)


async def get_story_repository(
    session: AsyncSession = Depends(get_database_session),
) -> StoryRepository:
    """
    Get story repository instance.
    
    Args:
        session: Database session
        
    Returns:
        StoryRepository interface
    """
    return StoryRepositoryImpl(session)


async def get_get_dashboard_stats_use_case(
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repository),
    project_repo: ProjectRepository = Depends(get_project_repository),
    story_repo: StoryRepository = Depends(get_story_repository),
) -> GetDashboardStatsUseCase:
    """
    Get GetDashboardStatsUseCase instance.
    
    Args:
        dashboard_repo: Dashboard repository for aggregated stats
        project_repo: Project repository for recent projects
        story_repo: Story repository for recent stories
        
    Returns:
        GetDashboardStatsUseCase instance
    """
    return GetDashboardStatsUseCase(dashboard_repo, project_repo, story_repo)