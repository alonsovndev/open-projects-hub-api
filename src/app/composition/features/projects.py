"""
Projects feature dependency composition.

All dependency wiring for project management use cases.

Dependencies:
- Infrastructure: Database session
- Repositories:
  - ProjectRepository (feature-specific, defined here)
  - ClientRepository (shared, cross-feature dependency)

Use Cases:
- Create Project: Initialize new project with client association
- List Projects: Retrieve all projects with client details
- Get Project: Retrieve single project by ID
- Update Project: Modify project details (includes client validation)
- Delete Project: Remove project

Cross-Feature Dependencies:
Projects depends on ClientRepository to validate that client_id exists
when creating or updating projects. This ensures referential integrity
at the application layer before database constraints.

Usage:
    from src.app.composition import get_create_project_use_case

    @router.post("")
    async def create_project(
        use_case: CreateProjectUseCase = Depends(get_create_project_use_case),
    ):
        return await use_case.execute(...)
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.composition.infrastructure import get_database_session
from src.app.composition.repositories import get_client_repository
from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.features.projects.application.use_cases.create_project import CreateProjectUseCase
from src.app.features.projects.application.use_cases.delete_project import DeleteProjectUseCase
from src.app.features.projects.application.use_cases.get_project_by_id import GetProjectByIdUseCase
from src.app.features.projects.application.use_cases.list_projects import ListProjectsUseCase
from src.app.features.projects.application.use_cases.update_project import UpdateProjectUseCase
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.projects.infrastructure.repositories.project_repository_impl import ProjectRepositoryImpl


# Feature-specific repository
async def get_project_repository(
    session: AsyncSession = Depends(get_database_session),
) -> ProjectRepository:
    """Project repository factory (feature-specific)."""

    return ProjectRepositoryImpl(session)


# Use case factories
async def get_create_project_use_case(
    project_repository: ProjectRepository = Depends(get_project_repository),
    client_repository: ClientRepository = Depends(get_client_repository),
) -> CreateProjectUseCase:
    """
    CreateProjectUseCase factory.

    Cross-feature dependency: Depends on ClientRepository to validate client exists.
    """
    return CreateProjectUseCase(project_repository, client_repository)


async def get_list_projects_use_case(
    repository: ProjectRepository = Depends(get_project_repository),
) -> ListProjectsUseCase:
    """ListProjectsUseCase factory."""
    return ListProjectsUseCase(repository)


async def get_project_by_id_use_case(
    repository: ProjectRepository = Depends(get_project_repository),
) -> GetProjectByIdUseCase:
    """GetProjectByIdUseCase factory."""
    return GetProjectByIdUseCase(repository)


async def get_update_project_use_case(
    project_repository: ProjectRepository = Depends(get_project_repository),
    client_repository: ClientRepository = Depends(get_client_repository),
) -> UpdateProjectUseCase:
    """
    UpdateProjectUseCase factory.

    Cross-feature dependency: Depends on ClientRepository to validate client exists.
    """
    return UpdateProjectUseCase(project_repository, client_repository)


async def get_delete_project_use_case(
    repository: ProjectRepository = Depends(get_project_repository),
) -> DeleteProjectUseCase:
    """DeleteProjectUseCase factory."""
    return DeleteProjectUseCase(repository)
