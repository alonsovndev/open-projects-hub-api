"""Project repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.app.features.projects.domain.entities.project_entity import ProjectEntity


class ProjectRepository(ABC):
    """Repository interface for Project aggregate."""

    @abstractmethod
    async def find_by_id(self, project_id: UUID) -> tuple[ProjectEntity, str] | None:
        """
        Find project by ID with client name.

        Args:
            project_id: Project UUID

        Returns:
            Tuple of (ProjectEntity, client_name) if found, None otherwise
        """

    @abstractmethod
    async def find_all(
        self,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
    ) -> list[tuple[ProjectEntity, str]]:
        """
        Find all projects with pagination and optional filtering.

        Args:
            limit: Maximum number of results (default 20)
            offset: Number of results to skip (default 0)
            status: Optional status filter (active, completed, archived)

        Returns:
            List of tuples (ProjectEntity, client_name)
        """

    @abstractmethod
    async def save(self, project: ProjectEntity) -> ProjectEntity | None:
        """
        Save or update a project.

        Args:
            project: ProjectEntity to save

        Returns:
            Saved ProjectEntity if successful, None otherwise
        """

    @abstractmethod
    async def delete(self, project_id: UUID) -> bool:
        """
        Delete a project by ID.

        Args:
            project_id: Project UUID

        Returns:
            True if deleted, False if not found or error
        """

    @abstractmethod
    async def count(self, status: str | None = None) -> int:
        """
        Count projects with optional status filter.

        Args:
            status: Optional status filter

        Returns:
            Number of projects
        """

    @abstractmethod
    async def exists(self, project_id: UUID) -> bool:
        """
        Check if a project exists by ID.

        Args:
            project_id: Project UUID

        Returns:
            True if the project exists, False otherwise
        """

    @abstractmethod
    async def get_story_counts(self, project_id: UUID) -> tuple[int, int]:
        """
        Get total and completed story counts for a project.

        Args:
            project_id: Project UUID

        Returns:
            Tuple of (total_stories, completed_stories)
        """

    @abstractmethod
    async def get_story_counts_batch(self, project_ids: list[UUID]) -> dict[UUID, tuple[int, int]]:
        """
        Get story counts for multiple projects in a single query.

        Args:
            project_ids: List of project UUIDs

        Returns:
            Dict mapping project_id to (total_stories, completed_stories)
        """
