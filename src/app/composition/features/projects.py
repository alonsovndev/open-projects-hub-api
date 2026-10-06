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
- Archive Project: Mark project as archived (excluded from active limits)
- Reactivate Project: Restore archived/completed project to active
- Regenerate Access Code: Replace the code clients use to open the Client Review page

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
from src.app.config.app_config import AppConfig
from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.features.projects.application.use_cases.archive_project import ArchiveProjectUseCase
from src.app.features.projects.application.use_cases.create_project import CreateProjectUseCase
from src.app.features.projects.application.use_cases.delete_project import DeleteProjectUseCase
from src.app.features.projects.application.use_cases.get_project_by_id import GetProjectByIdUseCase
from src.app.features.projects.application.use_cases.list_projects import ListProjectsUseCase
from src.app.features.projects.application.use_cases.reactivate_project import ReactivateProjectUseCase
from src.app.features.projects.application.use_cases.regenerate_access_code import RegenerateAccessCodeUseCase
from src.app.features.projects.application.use_cases.update_project import UpdateProjectUseCase
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.projects.infrastructure.repositories.project_repository_impl import ProjectRepositoryImpl


def _get_max_active_projects() -> int:
    """Read the active-project limit from application config."""
    config = AppConfig.instance()
    return config.get_config("project_limits.max_active_per_admin") or 3


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
    Injects active-project limit from configuration.
    """
    return CreateProjectUseCase(
        project_repository,
        client_repository,
        max_active_projects=_get_max_active_projects(),
    )


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


async def get_archive_project_use_case(
    repository: ProjectRepository = Depends(get_project_repository),
) -> ArchiveProjectUseCase:
    """ArchiveProjectUseCase factory."""
    return ArchiveProjectUseCase(repository)


async def get_reactivate_project_use_case(
    repository: ProjectRepository = Depends(get_project_repository),
) -> ReactivateProjectUseCase:
    """ReactivateProjectUseCase factory. Injects active-project limit from configuration."""
    return ReactivateProjectUseCase(repository, max_active_projects=_get_max_active_projects())


async def get_regenerate_access_code_use_case(
    repository: ProjectRepository = Depends(get_project_repository),
) -> RegenerateAccessCodeUseCase:
    """RegenerateAccessCodeUseCase factory."""
    return RegenerateAccessCodeUseCase(repository)
