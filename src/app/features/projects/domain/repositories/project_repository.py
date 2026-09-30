"""Project repository interface.

Every read, count and delete is confined to one workspace (`workspace_id`). A project of
another workspace behaves exactly like one that does not exist.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.app.features.projects.domain.entities.project_entity import ProjectEntity


class ProjectRepository(ABC):
    """Repository interface for Project aggregate."""

    @abstractmethod
    async def find_by_id(self, project_id: UUID, *, workspace_id: UUID) -> tuple[ProjectEntity, str] | None:
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
        *,
        workspace_id: UUID,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
        client_id: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        updated_from: datetime | None = None,
        updated_to: datetime | None = None,
        search: str | None = None,
    ) -> list[tuple[ProjectEntity, str]]:
        """
        Find all projects with pagination and optional filtering.

        Args:
            limit: Maximum number of results (default 20)
            offset: Number of results to skip (default 0)
            status: Optional status filter (active, completed, archived)
            client_id: Optional client UUID filter
            created_from: Optional lower bound on created_at
            created_to: Optional upper bound on created_at
            updated_from: Optional lower bound on updated_at
            updated_to: Optional upper bound on updated_at
            search: Optional substring match on name or code (case-insensitive)

        Returns:
            List of tuples (ProjectEntity, client_name)
        """

    @abstractmethod
    async def save(self, project: ProjectEntity) -> ProjectEntity:
        """
        Save or update a project.

        Args:
            project: ProjectEntity to save

        Returns:
            Saved ProjectEntity
        """

    @abstractmethod
    async def delete(self, project_id: UUID, *, workspace_id: UUID) -> bool:
        """
        Delete a project by ID.

        Args:
            project_id: Project UUID

        Returns:
            True if deleted, False if not found or error
        """

    @abstractmethod
    async def count(
        self,
        *,
        workspace_id: UUID,
        status: str | None = None,
        client_id: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        updated_from: datetime | None = None,
        updated_to: datetime | None = None,
        search: str | None = None,
    ) -> int:
        """
        Count projects with optional filters.

        Args:
            status: Optional status filter
            client_id: Optional client UUID filter
            created_from: Optional lower bound on created_at
            created_to: Optional upper bound on created_at
            updated_from: Optional lower bound on updated_at
            updated_to: Optional upper bound on updated_at
            search: Optional substring match on name or code (case-insensitive)

        Returns:
            Number of projects
        """

    @abstractmethod
    async def exists(self, project_id: UUID, *, workspace_id: UUID) -> bool:
        """
        Check if a project exists by ID.

        Args:
            project_id: Project UUID

        Returns:
            True if the project exists, False otherwise
        """

    @abstractmethod
    async def get_story_counts(self, project_id: UUID, *, workspace_id: UUID) -> tuple[int, int]:
        """
        Get total and completed story counts for a project.

        Args:
            project_id: Project UUID

        Returns:
            Tuple of (total_stories, completed_stories)
        """

    @abstractmethod
    async def get_story_counts_batch(
        self, project_ids: list[UUID], *, workspace_id: UUID
    ) -> dict[UUID, tuple[int, int]]:
        """
        Get story counts for multiple projects in a single query.

        Args:
            project_ids: List of project UUIDs

        Returns:
            Dict mapping project_id to (total_stories, completed_stories)
        """

    @abstractmethod
    async def count_active_by_workspace(self, workspace_id: UUID) -> int:
        """
        Count a workspace's active projects (the plan limit is per workspace, not per user).

        Args:
            workspace_id: Workspace UUID

        Returns:
            Number of active projects in the workspace
        """

    @abstractmethod
    async def has_active_projects_for_client(self, client_id: UUID, *, workspace_id: UUID) -> bool:
        """
        Check whether a client has any active projects.

        Args:
            client_id: Client UUID

        Returns:
            True if at least one active project exists for this client
        """

    @abstractmethod
    async def delete_archived_by_client(self, client_id: UUID, *, workspace_id: UUID) -> int:
        """
        Delete all archived projects for a client (cascade removes stories).

        Args:
            client_id: Client UUID

        Returns:
            Number of projects deleted
        """
