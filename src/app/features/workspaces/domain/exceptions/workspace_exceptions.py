"""Domain exceptions for workspaces feature."""


class WorkspaceNotFoundError(Exception):
    """Raised when a workspace cannot be found."""

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        super().__init__(f"Workspace not found: {workspace_id}")
