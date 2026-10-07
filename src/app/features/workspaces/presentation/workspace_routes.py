"""Workspace API routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.app.composition import get_update_workspace_use_case
from src.app.features.workspaces.application.dtos.workspace_dto import UpdateWorkspaceRequest, WorkspaceResponse
from src.app.features.workspaces.application.use_cases.update_workspace import UpdateWorkspaceUseCase
from src.app.features.workspaces.domain.exceptions.workspace_exceptions import WorkspaceNotFoundError
from src.app.shared.application.request_context import RequestContext
from src.app.shared.presentation.auth_dependencies import require_admin


router = APIRouter()


@router.patch("/me", response_model=WorkspaceResponse)
async def update_workspace(
    request: UpdateWorkspaceRequest,
    ctx: RequestContext = Depends(require_admin),
    use_case: UpdateWorkspaceUseCase = Depends(get_update_workspace_use_case),
) -> WorkspaceResponse:
    """
    Rename the caller's workspace.

    Requires ADMIN role. The workspace comes from the JWT, never from the path.

    Raises:
        401/403: Unauthorized or forbidden
        404: Workspace not found
        422: Invalid name
    """
    try:
        return await use_case.execute(request=request, ctx=ctx)
    except WorkspaceNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
