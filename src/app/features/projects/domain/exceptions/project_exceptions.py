"""Domain exceptions for projects feature."""

from src.app.shared.domain.exceptions.domain_exceptions import ConflictError


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


class ProjectCodeExistsError(ConflictError):
    """Raised when the workspace already has a project with this code (409)."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(f"A project with code '{code}' already exists")
