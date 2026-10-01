"""Tests for UpdateWorkspaceUseCase."""

from unittest.mock import AsyncMock

import pytest

from src.app.features.workspaces.application.dtos.workspace_dto import UpdateWorkspaceRequest
from src.app.features.workspaces.application.use_cases.update_workspace import UpdateWorkspaceUseCase
from src.app.features.workspaces.domain.entities.workspace_entity import WorkspaceEntity
from src.app.features.workspaces.domain.exceptions.workspace_exceptions import WorkspaceNotFoundError
from src.tests.support.request_context import make_request_context


class TestUpdateWorkspaceUseCase:
    @pytest.mark.asyncio
    async def test_renames_workspace_of_caller(self):
        ctx = make_request_context()
        workspace = WorkspaceEntity(id=ctx.workspace_id, name="Old")
        repository = AsyncMock()
        repository.find_by_id.return_value = workspace
        repository.update.side_effect = lambda entity: entity

        result = await UpdateWorkspaceUseCase(repository).execute(UpdateWorkspaceRequest(name=" New "), ctx)

        repository.find_by_id.assert_awaited_once_with(ctx.workspace_id)
        assert result.id == str(ctx.workspace_id.value)
        assert result.name == "New"

    @pytest.mark.asyncio
    async def test_raises_not_found_when_workspace_missing(self):
        repository = AsyncMock()
        repository.find_by_id.return_value = None

        with pytest.raises(WorkspaceNotFoundError):
            await UpdateWorkspaceUseCase(repository).execute(UpdateWorkspaceRequest(name="New"), make_request_context())

        repository.update.assert_not_awaited()
