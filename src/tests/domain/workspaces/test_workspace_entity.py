"""Tests for WorkspaceEntity.rename."""

import pytest

from src.app.features.workspaces.domain.entities.workspace_entity import WORKSPACE_NAME_MAX_LENGTH, WorkspaceEntity


class TestWorkspaceRename:
    def test_rename_strips_name_and_marks_updated(self):
        workspace = WorkspaceEntity.create("Old")
        previous_updated_at = workspace.updated_at

        workspace.rename("  New name  ")

        assert workspace.name == "New name"
        assert workspace.updated_at >= previous_updated_at

    @pytest.mark.parametrize("invalid_name", ["", "   ", "x" * (WORKSPACE_NAME_MAX_LENGTH + 1)])
    def test_rename_rejects_invalid_name_and_keeps_current(self, invalid_name):
        workspace = WorkspaceEntity.create("Old")

        with pytest.raises(ValueError):
            workspace.rename(invalid_name)

        assert workspace.name == "Old"
