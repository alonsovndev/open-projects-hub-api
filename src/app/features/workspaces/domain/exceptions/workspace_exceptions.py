"""Domain exceptions for workspaces feature."""

from src.app.shared.domain.exceptions.domain_exceptions import ConflictError


class WorkspaceNotFoundError(Exception):
    """Raised when a workspace cannot be found."""

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        super().__init__(f"Workspace not found: {workspace_id}")


class WorkspaceUserLimitExceededError(ConflictError):
    """Raised when adding a user would exceed the workspace's user cap (409)."""

    def __init__(self, limit: int):
        self.limit = limit
        super().__init__(f"This workspace has reached its limit of {limit} users. Remove a user to add another.")
