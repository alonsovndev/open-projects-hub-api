"""Domain exceptions for projects feature."""


class ProjectNotFoundError(Exception):
    """Raised when a project cannot be found."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        super().__init__(f"Project not found: {project_id}")


class ActiveProjectLimitExceededError(Exception):
    """Raised when creating/reactivating a project would exceed the active limit."""

    def __init__(self, limit: int):
        self.limit = limit
        super().__init__(f"Active project limit reached ({limit}). Archive a project before creating or reactivating.")
