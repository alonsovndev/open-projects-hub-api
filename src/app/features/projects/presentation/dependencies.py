"""Dependency injection for project feature."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.projects.application.use_cases.create_project import CreateProjectUseCase
from src.app.features.projects.application.use_cases.delete_project import DeleteProjectUseCase
from src.app.features.projects.application.use_cases.get_project_by_id import GetProjectByIdUseCase
from src.app.features.projects.application.use_cases.list_projects import ListProjectsUseCase
from src.app.features.projects.application.use_cases.update_project import UpdateProjectUseCase
from src.app.features.projects.infrastructure.repositories.project_repository_impl import ProjectRepositoryImpl
from src.app.shared.presentation.dependencies import get_database_session


async def get_project_repository(
    session: AsyncSession = Depends(get_database_session),
) -> ProjectRepositoryImpl:
    """
    Get project repository instance.
    
    Args:
        session: Database session
        
    Returns:
        ProjectRepositoryImpl instance
    """
    return ProjectRepositoryImpl(session)


async def get_create_project_use_case(
    repository: ProjectRepositoryImpl = Depends(get_project_repository),
) -> CreateProjectUseCase:
    """
    Get CreateProjectUseCase instance.
    
    Args:
        repository: Project repository
        
    Returns:
        CreateProjectUseCase instance
    """
    return CreateProjectUseCase(repository)


async def get_list_projects_use_case(
    repository: ProjectRepositoryImpl = Depends(get_project_repository),
) -> ListProjectsUseCase:
    """
    Get ListProjectsUseCase instance.
    
    Args:
        repository: Project repository
        
    Returns:
        ListProjectsUseCase instance
    """
    return ListProjectsUseCase(repository)


async def get_project_by_id_use_case(
    repository: ProjectRepositoryImpl = Depends(get_project_repository),
) -> GetProjectByIdUseCase:
    """
    Get GetProjectByIdUseCase instance.
    
    Args:
        repository: Project repository
        
    Returns:
        GetProjectByIdUseCase instance
    """
    return GetProjectByIdUseCase(repository)


async def get_update_project_use_case(
    repository: ProjectRepositoryImpl = Depends(get_project_repository),
) -> UpdateProjectUseCase:
    """
    Get UpdateProjectUseCase instance.
    
    Args:
        repository: Project repository
        
    Returns:
        UpdateProjectUseCase instance
    """
    return UpdateProjectUseCase(repository)


async def get_delete_project_use_case(
    repository: ProjectRepositoryImpl = Depends(get_project_repository),
) -> DeleteProjectUseCase:
    """
    Get DeleteProjectUseCase instance.
    
    Args:
        repository: Project repository
        
    Returns:
        DeleteProjectUseCase instance
    """
    return DeleteProjectUseCase(repository)
