"""
Workspaces feature dependency composition.

Use Cases:
- Update Workspace: Rename the caller's workspace
"""

from fastapi import Depends

from src.app.composition.repositories import get_workspace_repository
from src.app.features.workspaces.application.use_cases.update_workspace import UpdateWorkspaceUseCase
from src.app.features.workspaces.domain.repositories.workspace_repository import WorkspaceRepository


async def get_update_workspace_use_case(
    repository: WorkspaceRepository = Depends(get_workspace_repository),
) -> UpdateWorkspaceUseCase:
    """UpdateWorkspaceUseCase factory."""
    return UpdateWorkspaceUseCase(repository)
