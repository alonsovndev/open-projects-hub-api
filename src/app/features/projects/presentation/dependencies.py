"""Dependency injection for project feature."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.projects.application.use_cases.create_project import CreateProjectUseCase
from src.app.features.projects.application.use_cases.delete_project import DeleteProjectUseCase
from src.app.features.projects.application.use_cases.get_project_by_id import GetProjectByIdUseCase
from src.app.features.projects.application.use_cases.list_projects import ListProjectsUseCase
from src.app.features.projects.application.use_cases.update_project import UpdateProjectUseCase
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.projects.infrastructure.repositories.project_repository_impl import ProjectRepositoryImpl
from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.features.clients.infrastructure.repositories.client_repository_impl import ClientRepositoryImpl
from src.app.shared.persistence.db_session import get_database_session


async def get_project_repository(
    session: AsyncSession = Depends(get_database_session),
) -> ProjectRepository:
    """Get project repository instance."""
    return ProjectRepositoryImpl(session)


async def get_client_repository(
    session: AsyncSession = Depends(get_database_session),
) -> ClientRepository:
    """Get client repository instance."""
    return ClientRepositoryImpl(session)


async def get_create_project_use_case(
    project_repository: ProjectRepository = Depends(get_project_repository),
    client_repository: ClientRepository = Depends(get_client_repository),
) -> CreateProjectUseCase:
    """Get CreateProjectUseCase instance."""
    return CreateProjectUseCase(project_repository, client_repository)


async def get_list_projects_use_case(
    repository: ProjectRepository = Depends(get_project_repository),
) -> ListProjectsUseCase:
    """Get ListProjectsUseCase instance."""
    return ListProjectsUseCase(repository)


async def get_project_by_id_use_case(
    repository: ProjectRepository = Depends(get_project_repository),
) -> GetProjectByIdUseCase:
    """Get GetProjectByIdUseCase instance."""
    return GetProjectByIdUseCase(repository)


async def get_update_project_use_case(
    project_repository: ProjectRepository = Depends(get_project_repository),
    client_repository: ClientRepository = Depends(get_client_repository),
) -> UpdateProjectUseCase:
    """Get UpdateProjectUseCase instance."""
    return UpdateProjectUseCase(project_repository, client_repository)


async def get_delete_project_use_case(
    repository: ProjectRepository = Depends(get_project_repository),
) -> DeleteProjectUseCase:
    """Get DeleteProjectUseCase instance."""
    return DeleteProjectUseCase(repository)
