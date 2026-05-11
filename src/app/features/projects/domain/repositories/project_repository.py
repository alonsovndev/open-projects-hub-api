"""Project repository interface."""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.app.features.projects.domain.entities.project_entity import ProjectEntity


class ProjectRepository(ABC):
    """Repository interface for Project aggregate."""
    
    @abstractmethod
    async def find_by_id(self, project_id: UUID) -> Optional[ProjectEntity]:
        """
        Find project by ID.
        
        Args:
            project_id: Project UUID
            
        Returns:
            ProjectEntity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_all(
        self,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> List[ProjectEntity]:
        """
        Find all projects with pagination and optional filtering.
        
        Args:
            limit: Maximum number of results (default 20)
            offset: Number of results to skip (default 0)
            status: Optional status filter (active, completed, archived)
            
        Returns:
            List of ProjectEntity objects
        """
        pass
    
    @abstractmethod
    async def save(self, project: ProjectEntity) -> Optional[ProjectEntity]:
        """
        Save or update a project.
        
        Args:
            project: ProjectEntity to save
            
        Returns:
            Saved ProjectEntity if successful, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, project_id: UUID) -> bool:
        """
        Delete a project by ID.
        
        Args:
            project_id: Project UUID
            
        Returns:
            True if deleted, False if not found or error
        """
        pass
    
    @abstractmethod
    async def count(self, status: Optional[str] = None) -> int:
        """
        Count projects with optional status filter.
        
        Args:
            status: Optional status filter
            
        Returns:
            Number of projects
        """
        pass
