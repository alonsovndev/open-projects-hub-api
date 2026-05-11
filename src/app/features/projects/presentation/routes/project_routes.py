"""Project routes."""
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.params import Depends

from src.app.features.projects.application.dtos.project_dto import (
    CreateProjectRequest,
    ProjectResponse,
    UpdateProjectRequest,
)
from src.app.features.projects.application.use_cases.create_project import CreateProjectUseCase
from src.app.features.projects.application.use_cases.delete_project import DeleteProjectUseCase
from src.app.features.projects.application.use_cases.get_project_by_id import GetProjectByIdUseCase
from src.app.features.projects.application.use_cases.list_projects import ListProjectsUseCase
from src.app.features.projects.application.use_cases.update_project import UpdateProjectUseCase
from src.app.features.projects.presentation.dependencies import (
    get_create_project_use_case,
    get_delete_project_use_case,
    get_list_projects_use_case,
    get_project_by_id_use_case,
    get_update_project_use_case,
)
from src.app.features.user.presentation.auth_dependencies import get_current_user, require_admin
from src.app.shared.presentation.base_handler import BaseRouteHandler

router = APIRouter()
handler = BaseRouteHandler()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: CreateProjectRequest,
    current_user: Dict[str, Any] = Depends(require_admin),
    use_case: CreateProjectUseCase = Depends(get_create_project_use_case),
) -> ProjectResponse:
    """
    Create a new project (admin only).
    
    Requires ADMIN role. Created by user from JWT token.
    
    Args:
        payload: CreateProjectRequest with project details
        current_user: Current authenticated admin user
        use_case: Injected CreateProjectUseCase
        
    Returns:
        ProjectResponse with created project data
        
    Raises:
        400: Validation failed
        401/403: Unauthorized or forbidden
        500: Internal server error
    """
    return await handler.execute_with_payload_extraction(
        execute_fn=lambda user_id: use_case.execute(
            name=payload.name,
            created_by=user_id,
            description=payload.description,
            start_date=payload.start_date,
            end_date=payload.end_date,
        ),
        current_user=current_user,
    )


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = Query(default=None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    use_case: ListProjectsUseCase = Depends(get_list_projects_use_case),
) -> list[ProjectResponse]:
    """
    List projects with pagination.
    
    Requires authentication. Supports filtering by status.
    
    Args:
        limit: Maximum number of results (1-100, default 20)
        offset: Number of results to skip (default 0)
        status: Optional status filter (active, completed, archived)
        current_user: Current authenticated user
        use_case: Injected ListProjectsUseCase
        
    Returns:
        List of ProjectResponse objects
        
    Raises:
        400: Invalid query parameters
        401: Unauthorized
        500: Internal server error
    """
    async def execute():
        # Validate status if provided
        if status and status not in ["active", "completed", "archived"]:
            raise ValueError("Status must be one of: active, completed, archived")
        
        return await use_case.execute(
            limit=limit,
            offset=offset,
            status=status,
        )
    
    return await handler.execute(execute)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_by_id(
    project_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    use_case: GetProjectByIdUseCase = Depends(get_project_by_id_use_case),
) -> ProjectResponse:
    """
    Get project by ID.
    
    Requires authentication.
    
    Args:
        project_id: Project UUID
        current_user: Current authenticated user
        use_case: Injected GetProjectByIdUseCase
        
    Returns:
        ProjectResponse with project data
        
    Raises:
        400: Invalid UUID
        401: Unauthorized
        404: Project not found
        500: Internal server error
    """
    async def execute():
        result = await use_case.execute(str(project_id))
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return result
    
    return await handler.execute(execute)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    payload: UpdateProjectRequest,
    current_user: Dict[str, Any] = Depends(require_admin),
    use_case: UpdateProjectUseCase = Depends(get_update_project_use_case),
) -> ProjectResponse:
    """
    Update project (admin only).
    
    Requires ADMIN role. Supports partial updates.
    
    Args:
        project_id: Project UUID
        payload: UpdateProjectRequest with fields to update
        current_user: Current authenticated admin user
        use_case: Injected UpdateProjectUseCase
        
    Returns:
        ProjectResponse with updated project data
        
    Raises:
        400: Validation failed
        401/403: Unauthorized or forbidden
        404: Project not found
        500: Internal server error
    """
    async def execute():
        result = await use_case.execute(
            project_id=str(project_id),
            name=payload.name,
            description=payload.description,
            status=payload.status,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return result
    
    return await handler.execute(execute)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: Dict[str, Any] = Depends(require_admin),
    use_case: DeleteProjectUseCase = Depends(get_delete_project_use_case),
) -> None:
    """
    Delete project (admin only).
    
    Requires ADMIN role. Cascade deletes all related stories.
    
    Args:
        project_id: Project UUID
        current_user: Current authenticated admin user
        use_case: Injected DeleteProjectUseCase
        
    Raises:
        400: Invalid UUID
        401/403: Unauthorized or forbidden
        404: Project not found
        500: Internal server error
    """
    async def execute():
        deleted = await use_case.execute(str(project_id))
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
    
    await handler.execute(execute)
