"""Story draft repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.value_objects.draft_status import DraftStatus


class StoryDraftRepository(ABC):
    """Repository interface for StoryDraft aggregate."""

    @abstractmethod
    async def find_by_id(self, draft_id: UUID) -> StoryDraftEntity | None:
        """
        Find story draft by ID.

        Args:
            draft_id: Draft UUID

        Returns:
            StoryDraftEntity if found, None otherwise
        """

    @abstractmethod
    async def find_by_project(
        self,
        project_id: UUID,
        status: DraftStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[StoryDraftEntity]:
        """
        Find story drafts for a project.

        Args:
            project_id: Project UUID
            status: Restrict to a single draft status, or None for all
            limit: Maximum results
            offset: Number to skip

        Returns:
            List of StoryDraftEntity objects
        """

    @abstractmethod
    async def find_active_by_user(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[StoryDraftEntity]:
        """
        Find active (non-applied) drafts by user.

        Args:
            user_id: User UUID
            limit: Maximum results
            offset: Number to skip

        Returns:
            List of StoryDraftEntity objects
        """

    @abstractmethod
    async def save(self, draft: StoryDraftEntity) -> StoryDraftEntity:
        """
        Save or update a story draft.

        Args:
            draft: StoryDraftEntity to save

        Returns:
            Saved StoryDraftEntity
        """

    @abstractmethod
    async def delete(self, draft_id: UUID) -> bool:
        """
        Delete a story draft.

        Args:
            draft_id: Draft UUID

        Returns:
            True if deleted, False if not found
        """

    @abstractmethod
    async def count_by_project(self, project_id: UUID, status: DraftStatus | None = None) -> int:
        """
        Count drafts for a project.

        Args:
            project_id: Project UUID
            status: Restrict to a single draft status, or None for all

        Returns:
            Number of drafts
        """
