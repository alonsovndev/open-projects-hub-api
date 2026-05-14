"""
Unit of Work pattern interface.

Provides transaction management across multiple repositories,
ensuring atomicity for operations that span multiple aggregates.
"""
from abc import ABC, abstractmethod
from typing import Optional

from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.features.user.domain.repositories.user_preferences_repository import UserPreferencesRepository


class UnitOfWork(ABC):
    """
    Abstract Unit of Work for managing transactions across repositories.
    
    The Unit of Work pattern coordinates writes across multiple repositories,
    ensuring that all changes within a transaction succeed or fail together.
    
    Usage:
        async with uow:
            project = await uow.projects.find_by_id(project_id)
            story = await uow.stories.find_by_id(story_id)
            # ... modify entities ...
            await uow.projects.save(project)
            await uow.stories.save(story)
            await uow.commit()  # Atomic commit
    """
    
    # Repository properties - lazily initialized
    projects: ProjectRepository
    stories: StoryRepository
    users: UserRepository
    user_preferences: UserPreferencesRepository
    
    @abstractmethod
    async def __aenter__(self):
        """
        Enter async context manager - start transaction.
        
        Returns:
            Self for context manager protocol
        """
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit async context manager - rollback on exception.
        
        Args:
            exc_type: Exception type if raised
            exc_val: Exception value if raised
            exc_tb: Exception traceback if raised
        """
        pass
    
    @abstractmethod
    async def commit(self) -> None:
        """
        Commit the current transaction.
        
        Persists all changes made through repositories within this unit of work.
        Should be called explicitly before exiting the context manager.
        
        Raises:
            Exception: If commit fails due to constraint violations or database errors
        """
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """
        Rollback the current transaction.
        
        Discards all changes made through repositories within this unit of work.
        Called automatically if an exception occurs before commit.
        """
        pass
