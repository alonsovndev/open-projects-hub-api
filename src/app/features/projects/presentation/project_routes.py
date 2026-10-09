"""Project routes."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.params import Depends

from src.app.composition import (
    get_archive_project_use_case,
    get_create_project_use_case,
    get_delete_project_use_case,
    get_list_projects_use_case,
    get_project_by_id_use_case,
    get_reactivate_project_use_case,
    get_regenerate_access_code_use_case,
    get_update_project_use_case,
)
from src.app.features.projects.application.dtos.project_dto import (
    CreateProjectRequest,
    ProjectResponse,
    UpdateProjectRequest,
)
from src.app.features.projects.application.use_cases.archive_project import ArchiveProjectUseCase
from src.app.features.projects.application.use_cases.create_project import CreateProjectUseCase
from src.app.features.projects.application.use_cases.delete_project import DeleteProjectUseCase
from src.app.features.projects.application.use_cases.get_project_by_id import GetProjectByIdUseCase
from src.app.features.projects.application.use_cases.list_projects import ListProjectsUseCase
from src.app.features.projects.application.use_cases.reactivate_project import ReactivateProjectUseCase
from src.app.features.projects.application.use_cases.regenerate_access_code import RegenerateAccessCodeUseCase
from src.app.features.projects.application.use_cases.update_project import UpdateProjectUseCase
from src.app.features.projects.domain.exceptions.project_exceptions import (
    ActiveProjectLimitExceededError,
    ProjectNotFoundError,
)
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.shared.application.dtos.pagination_dto import PaginatedResponse
from src.app.shared.application.request_context import RequestContext
from src.app.shared.domain.exceptions.domain_exceptions import NotFoundError, ValidationError
from src.app.shared.presentation.auth_dependencies import get_request_context, require_editor


router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: CreateProjectRequest,
    ctx: RequestContext = Depends(require_editor),
    use_case: CreateProjectUseCase = Depends(get_create_project_use_case),
) -> ProjectResponse:
    """
    Create a new project.

    Requires ADMIN role. The created_by user is extracted from the JWT token.

    Args:
        payload: CreateProjectRequest with project details (name, code, client_id, optional fields)
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected CreateProjectUseCase

    Returns:
        ProjectResponse with created project data (id, name, status, timestamps)

    Raises:
        400: Validation failed (invalid name, dates, etc.)
        401/403: Unauthorized or forbidden
        500: Internal server error
    """
    try:
        return await use_case.execute(request=payload, ctx=ctx)
    except ActiveProjectLimitExceededError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    project_status: str | None = Query(default=None, alias="status"),
    client_id: UUID | None = Query(default=None, alias="clientId"),
    created_from: datetime | None = Query(default=None, alias="createdFrom"),
    created_to: datetime | None = Query(default=None, alias="createdTo"),
    updated_from: datetime | None = Query(default=None, alias="updatedFrom"),
    updated_to: datetime | None = Query(default=None, alias="updatedTo"),
    search: str | None = Query(default=None, max_length=100),
    ctx: RequestContext = Depends(get_request_context),
    use_case: ListProjectsUseCase = Depends(get_list_projects_use_case),
) -> PaginatedResponse[ProjectResponse]:
    """
    List projects with pagination and optional filters.

    Requires authentication.

    Args:
        limit: Maximum number of results (1-100, default 20)
        offset: Number of results to skip (default 0)
        project_status: Optional status filter (active, completed, archived)
        client_id: Optional client UUID filter
        created_from: Optional lower bound on created_at (ISO datetime)
        created_to: Optional upper bound on created_at (ISO datetime)
        updated_from: Optional lower bound on updated_at (ISO datetime)
        updated_to: Optional upper bound on updated_at (ISO datetime)
        search: Optional substring match on name or code (case-insensitive)
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected ListProjectsUseCase

    Returns:
        PaginatedResponse containing pagination metadata and list of ProjectResponse objects

    Raises:
        400: Invalid query parameters
        401: Unauthorized
        500: Internal server error
    """
    valid_statuses = [status.value for status in ProjectStatus]
    if project_status and project_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Status must be one of: {', '.join(valid_statuses)}",
        )

    return await use_case.execute(
        ctx=ctx,
        limit=limit,
        offset=offset,
        status=project_status,
        client_id=str(client_id) if client_id else None,
        created_from=created_from,
        created_to=created_to,
        updated_from=updated_from,
        updated_to=updated_to,
        search=search,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_by_id(
    project_id: UUID,
    ctx: RequestContext = Depends(get_request_context),
    use_case: GetProjectByIdUseCase = Depends(get_project_by_id_use_case),
) -> ProjectResponse:
    """
    Get project by ID.

    Requires authentication.

    Args:
        project_id: Project UUID
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected GetProjectByIdUseCase

    Returns:
        ProjectResponse with project data

    Raises:
        400: Invalid UUID
        401: Unauthorized
        404: Project not found
        500: Internal server error
    """
    result = await use_case.execute(str(project_id), ctx=ctx)

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return result


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    payload: UpdateProjectRequest,
    ctx: RequestContext = Depends(require_editor),
    use_case: UpdateProjectUseCase = Depends(get_update_project_use_case),
) -> ProjectResponse:
    """
    Update project.

    Requires ADMIN role. Supports partial updates — only provided fields are changed.

    Args:
        project_id: Project UUID
        payload: UpdateProjectRequest with fields to update
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected UpdateProjectUseCase

    Returns:
        ProjectResponse with updated project data

    Raises:
        400: Validation failed
        401/403: Unauthorized or forbidden
        404: Project not found
        500: Internal server error
    """
    try:
        return await use_case.execute(project_id=str(project_id), request=payload, ctx=ctx)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    ctx: RequestContext = Depends(require_editor),
    use_case: DeleteProjectUseCase = Depends(get_delete_project_use_case),
) -> None:
    """
    Delete project.

    Requires ADMIN role. Cascade deletes all related stories.

    Args:
        project_id: Project UUID
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected DeleteProjectUseCase

    Raises:
        400: Invalid UUID
        401/403: Unauthorized or forbidden
        404: Project not found
        500: Internal server error
    """
    try:
        await use_case.execute(project_id=str(project_id), ctx=ctx)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{project_id}/archive", response_model=ProjectResponse)
async def archive_project(
    project_id: UUID,
    ctx: RequestContext = Depends(require_editor),
    use_case: ArchiveProjectUseCase = Depends(get_archive_project_use_case),
) -> ProjectResponse:
    """
    Archive a project, excluding it from active-project limits.

    Requires ADMIN role.

    Raises:
        404: Project not found
        401/403: Unauthorized or forbidden
    """
    try:
        return await use_case.execute(project_id=str(project_id), ctx=ctx)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{project_id}/reactivate", response_model=ProjectResponse)
async def reactivate_project(
    project_id: UUID,
    ctx: RequestContext = Depends(require_editor),
    use_case: ReactivateProjectUseCase = Depends(get_reactivate_project_use_case),
) -> ProjectResponse:
    """
    Reactivate an archived or completed project.

    Requires ADMIN role. Subject to active-project limit enforcement (BE-002).

    Raises:
        404: Project not found
        409: Active project limit exceeded
        401/403: Unauthorized or forbidden
    """
    try:
        return await use_case.execute(project_id=str(project_id), ctx=ctx)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ActiveProjectLimitExceededError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.post("/{project_id}/access-code/regenerate", response_model=ProjectResponse)
async def regenerate_access_code(
    project_id: UUID,
    ctx: RequestContext = Depends(require_editor),
    use_case: RegenerateAccessCodeUseCase = Depends(get_regenerate_access_code_use_case),
) -> ProjectResponse:
    """
    Replace the project's access code.

    The previous code and any link built from it stop working immediately. Use this when a
    code was shared with someone who should no longer see the project.

    Raises:
        404: Project not found
        401/403: Unauthorized or forbidden
    """
    try:
        return await use_case.execute(project_id=str(project_id), ctx=ctx)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
