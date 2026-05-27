"""Story repository interface."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
from uuid import UUID

if TYPE_CHECKING:
    from src.app.features.stories.domain.entities.story_entity import StoryEntity


class StoryRepository(ABC):
    """Abstract repository interface for Story entities."""

    @abstractmethod
    async def find_by_id(self, story_id: UUID) -> Optional["StoryEntity"]:
        """
        Find story by ID.

        Args:
            story_id: Story UUID

        Returns:
            StoryEntity if found, None otherwise
        """

    @abstractmethod
    async def find_all(
        self,
        limit: int = 20,
        offset: int = 0,
        project_id: UUID | None = None,
        status: str | None = None,
        priority: str | None = None,
        assigned_to: UUID | None = None,
    ) -> list["StoryEntity"]:
        """
        Find all stories with pagination and optional filtering.

        Args:
            limit: Maximum number of results (default 20)
            offset: Number of results to skip (default 0)
            project_id: Optional project filter
            status: Optional status filter (todo, in_progress, done)
            priority: Optional priority filter (low, medium, high)
            assigned_to: Optional assigned user filter

        Returns:
            List of StoryEntity objects
        """

    @abstractmethod
    async def find_by_project_id(
        self,
        project_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list["StoryEntity"]:
        """
        Find all stories for a specific project.

        Args:
            project_id: Project UUID
            limit: Maximum number of results (default 20)
            offset: Number of results to skip (default 0)

        Returns:
            List of StoryEntity objects
        """

    @abstractmethod
    async def find_by_assigned_user(self, user_id: UUID) -> list["StoryEntity"]:
        """
        Find all stories assigned to a specific user.

        Args:
            user_id: User UUID

        Returns:
            List of StoryEntity objects
        """

    @abstractmethod
    async def save(self, story: "StoryEntity") -> Optional["StoryEntity"]:
        """
        Save or update a story.

        Args:
            story: StoryEntity to save

        Returns:
            Saved StoryEntity if successful, None otherwise
        """

    @abstractmethod
    async def delete(self, story_id: UUID) -> bool:
        """
        Delete a story by ID.

        Args:
            story_id: Story UUID

        Returns:
            True if deleted, False if not found or error
        """

    @abstractmethod
    async def count(
        self,
        project_id: UUID | None = None,
        status: str | None = None,
        priority: str | None = None,
        assigned_to: UUID | None = None,
    ) -> int:
        """
        Count stories with optional filters.

        Args:
            project_id: Optional project filter
            status: Optional status filter
            priority: Optional priority filter
            assigned_to: Optional assigned user filter

        Returns:
            Number of stories matching filters
        """
