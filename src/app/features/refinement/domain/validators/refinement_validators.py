"""Refinement domain validators."""


class RefinementValidators:
    """Centralized validation rules for refinement entities and DTOs."""
    
    # Validation constants
    MIN_TITLE_LENGTH = 1
    MAX_TITLE_LENGTH = 500
    MIN_NOTES_LENGTH = 20
    
    @staticmethod
    def validate_title(title: str) -> None:
        """
        Validate story draft title.
        
        Args:
            title: Title to validate
            
        Raises:
            ValueError: If title is invalid
        """
        if not title or not title.strip():
            raise ValueError("Story title cannot be empty")
        
        if len(title) > RefinementValidators.MAX_TITLE_LENGTH:
            raise ValueError(f"Story title cannot exceed {RefinementValidators.MAX_TITLE_LENGTH} characters")
    
    @staticmethod
    def validate_raw_notes(raw_notes: str) -> None:
        """
        Validate raw discovery notes.
        
        Args:
            raw_notes: Notes to validate
            
        Raises:
            ValueError: If notes are invalid
        """
        if not raw_notes or not raw_notes.strip():
            raise ValueError("Raw notes cannot be empty")
        
        if len(raw_notes) < RefinementValidators.MIN_NOTES_LENGTH:
            raise ValueError(f"Raw notes must be at least {RefinementValidators.MIN_NOTES_LENGTH} characters")
    
    @staticmethod
    def validate_project_id(project_id: str) -> None:
        """
        Validate project ID.
        
        Args:
            project_id: Project ID to validate
            
        Raises:
            ValueError: If project ID is invalid
        """
        if not project_id or not project_id.strip():
            raise ValueError("Project ID is required")
