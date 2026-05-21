"""Story draft repository interface."""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity


class StoryDraftRepository(ABC):
    """Repository interface for StoryDraft aggregate."""
    
    @abstractmethod
    async def find_by_id(self, draft_id: UUID) -> Optional[StoryDraftEntity]:
        """
        Find story draft by ID.
        
        Args:
            draft_id: Draft UUID
            
        Returns:
            StoryDraftEntity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_by_project(
        self,
        project_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> List[StoryDraftEntity]:
        """
        Find story drafts for a project.
        
        Args:
            project_id: Project UUID
            limit: Maximum results
            offset: Number to skip
            
        Returns:
            List of StoryDraftEntity objects
        """
        pass
    
    @abstractmethod
    async def find_active_by_user(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> List[StoryDraftEntity]:
        """
        Find active (non-applied) drafts by user.
        
        Args:
            user_id: User UUID
            limit: Maximum results
            offset: Number to skip
            
        Returns:
            List of StoryDraftEntity objects
        """
        pass
    
    @abstractmethod
    async def save(self, draft: StoryDraftEntity) -> StoryDraftEntity:
        """
        Save or update a story draft.
        
        Args:
            draft: StoryDraftEntity to save
            
        Returns:
            Saved StoryDraftEntity
        """
        pass
    
    @abstractmethod
    async def delete(self, draft_id: UUID) -> bool:
        """
        Delete a story draft.
        
        Args:
            draft_id: Draft UUID
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def count_by_project(self, project_id: UUID) -> int:
        """
        Count drafts for a project.
        
        Args:
            project_id: Project UUID
            
        Returns:
            Number of drafts
        """
        pass
