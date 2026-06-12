"""Domain exceptions for projects feature."""


class ProjectNotFoundError(Exception):
    """Raised when a project cannot be found."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        super().__init__(f"Project not found: {project_id}")
