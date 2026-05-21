"""Story draft entity - domain model for AI refinement drafts."""
from datetime import datetime
from typing import List, Optional

from src.app.features.refinement.domain.value_objects.refinement_status import RefinementStatus
from src.app.features.refinement.domain.validators.refinement_validators import RefinementValidators
from src.app.shared.domain.entities.base_entity import BaseEntity
from src.app.shared.domain.value_objects.entity_id import EntityId


class StoryDraftEntity(BaseEntity):
    """
    Story draft entity representing a user story being refined with AI.
    
    Drafts go through a lifecycle: draft -> refining -> refined -> applied.
    AI suggestions are attached to help improve the story quality.
    """
    
    def __init__(
        self,
        id: EntityId,
        title: str,
        description: Optional[str],
        acceptance_criteria: List[str],
        project_id: EntityId,
        created_by: EntityId,
        status: RefinementStatus,
        refined_title: Optional[str] = None,
        refined_description: Optional[str] = None,
        refined_criteria: Optional[List[str]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """
        Initialize StoryDraftEntity.
        
        Args:
            id: Unique draft identifier
            title: Raw story title from user
            description: Raw story description
            acceptance_criteria: List of acceptance criteria
            project_id: Associated project ID
            created_by: User ID of creator
            status: Current refinement status
            refined_title: AI-refined title (if refined)
            refined_description: AI-refined description (if refined)
            refined_criteria: AI-refined acceptance criteria (if refined)
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        RefinementValidators.validate_title(title)
        
        now = datetime.now()
        super().__init__(
            id=id,
            created_at=created_at or now,
            updated_at=updated_at or now,
        )
        
        self._title = title
        self._description = description
        self._acceptance_criteria = acceptance_criteria or []
        self._project_id = project_id
        self._created_by = created_by
        self._status = status
        self._refined_title = refined_title
        self._refined_description = refined_description
        self._refined_criteria = refined_criteria
    
    @property
    def title(self) -> str:
        """Get raw story title."""
        return self._title
    
    @property
    def description(self) -> Optional[str]:
        """Get raw story description."""
        return self._description
    
    @property
    def acceptance_criteria(self) -> List[str]:
        """Get acceptance criteria."""
        return self._acceptance_criteria
    
    @property
    def project_id(self) -> EntityId:
        """Get associated project ID."""
        return self._project_id
    
    @property
    def created_by(self) -> EntityId:
        """Get creator user ID."""
        return self._created_by
    
    @property
    def status(self) -> RefinementStatus:
        """Get refinement status."""
        return self._status
    
    @property
    def refined_title(self) -> Optional[str]:
        """Get AI-refined title."""
        return self._refined_title
    
    @property
    def refined_description(self) -> Optional[str]:
        """Get AI-refined description."""
        return self._refined_description
    
    @property
    def refined_criteria(self) -> Optional[List[str]]:
        """Get AI-refined acceptance criteria."""
        return self._refined_criteria
    
    def start_refinement(self) -> None:
        """Mark draft as being refined."""
        self._status = RefinementStatus.REFINING
        self.mark_as_updated()
    
    def apply_refinement(
        self,
        refined_title: str,
        refined_description: Optional[str] = None,
        refined_criteria: Optional[List[str]] = None,
    ) -> None:
        """
        Apply AI refinement results to the draft.
        
        Args:
            refined_title: AI-refined title
            refined_description: AI-refined description
            refined_criteria: AI-refined acceptance criteria
        """
        self._refined_title = refined_title
        self._refined_description = refined_description
        self._refined_criteria = refined_criteria
        self._status = RefinementStatus.REFINED
        self.mark_as_updated()
    
    def mark_applied(self) -> None:
        """Mark the refined story as applied (converted to real story)."""
        self._status = RefinementStatus.APPLIED
        self.mark_as_updated()
    
    def update_draft(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        acceptance_criteria: Optional[List[str]] = None,
    ) -> None:
        """
        Update draft fields.
        
        Args:
            title: New title
            description: New description
            acceptance_criteria: New acceptance criteria
        """
        if title is not None:
            RefinementValidators.validate_title(title)
            self._title = title
        
        if description is not None:
            self._description = description
        
        if acceptance_criteria is not None:
            self._acceptance_criteria = acceptance_criteria
        
        # Reset refinement status if draft is modified
        if self._status == RefinementStatus.REFINED:
            self._status = RefinementStatus.DRAFT
            self._refined_title = None
            self._refined_description = None
            self._refined_criteria = None
        
        self.mark_as_updated()
    
    @classmethod
    def create(
        cls,
        title: str,
        project_id: EntityId,
        created_by: EntityId,
        description: Optional[str] = None,
        acceptance_criteria: Optional[List[str]] = None,
    ) -> "StoryDraftEntity":
        """
        Factory method to create a new story draft.
        
        Args:
            title: Story title
            project_id: Associated project ID
            created_by: User ID of creator
            description: Optional description
            acceptance_criteria: Optional acceptance criteria
            
        Returns:
            New StoryDraftEntity instance
        """
        return cls(
            id=EntityId.generate(),
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria or [],
            project_id=project_id,
            created_by=created_by,
            status=RefinementStatus.default(),
        )
