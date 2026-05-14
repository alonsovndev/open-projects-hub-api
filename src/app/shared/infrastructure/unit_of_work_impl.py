"""
SQLAlchemy implementation of Unit of Work pattern.

Manages database transactions across multiple repositories using
a shared AsyncSession for atomic operations.
"""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.projects.infrastructure.repositories.project_repository_impl import ProjectRepositoryImpl
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.stories.infrastructure.repositories.story_repository_impl import StoryRepositoryImpl
from src.app.features.user.domain.repositories.user_preferences_repository import UserPreferencesRepository
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.features.user.infrastructure.repositories.user_preferences_repository_impl import UserPreferencesRepositoryImpl
from src.app.features.user.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from src.app.shared.domain.unit_of_work import UnitOfWork
from src.app.shared.utils.log_util import log


class SqlAlchemyUnitOfWork(UnitOfWork):
    """
    SQLAlchemy implementation of Unit of Work.
    
    Manages a single database session shared across all repositories,
    providing transaction boundaries for atomic multi-repository operations.
    
    Example:
        async with uow:
            # All operations share the same transaction
            project = await uow.projects.find_by_id(project_id)
            project.status = "completed"
            await uow.projects.save(project)
            
            # Update related stories atomically
            stories = await uow.stories.find_by_project_id(project_id)
            for story in stories:
                story.status = "done"
                await uow.stories.save(story)
            
            # Commit all changes together
            await uow.commit()
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize Unit of Work with database session.
        
        Args:
            session: SQLAlchemy async session for transaction management
        """
        self._session = session
        self._committed = False
        self._rolled_back = False
        
        # Initialize repository references (lazy loaded)
        self._projects: Optional[ProjectRepository] = None
        self._stories: Optional[StoryRepository] = None
        self._users: Optional[UserRepository] = None
        self._user_preferences: Optional[UserPreferencesRepository] = None
    
    @property
    def projects(self) -> ProjectRepository:
        """Get or create projects repository."""
        if self._projects is None:
            self._projects = ProjectRepositoryImpl(self._session)
        return self._projects
    
    @property
    def stories(self) -> StoryRepository:
        """Get or create stories repository."""
        if self._stories is None:
            self._stories = StoryRepositoryImpl(self._session)
        return self._stories
    
    @property
    def users(self) -> UserRepository:
        """Get or create users repository."""
        if self._users is None:
            self._users = UserRepositoryImpl(self._session)
        return self._users
    
    @property
    def user_preferences(self) -> UserPreferencesRepository:
        """Get or create user preferences repository."""
        if self._user_preferences is None:
            self._user_preferences = UserPreferencesRepositoryImpl(self._session)
        return self._user_preferences
    
    async def __aenter__(self):
        """
        Enter context manager - start transaction.
        
        Returns:
            Self for use in async with statement
        """
        # SQLAlchemy session already manages transaction boundaries
        # Transaction begins implicitly on first query/operation
        log.debug("UnitOfWork: Entering transaction context")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context manager - handle transaction completion.
        
        Automatically rolls back if exception occurred and commit wasn't called.
        
        Args:
            exc_type: Exception type if raised
            exc_val: Exception value if raised  
            exc_tb: Exception traceback if raised
        """
        if exc_type is not None:
            # Exception occurred - rollback if not already done
            if not self._rolled_back and not self._committed:
                log.warning(
                    f"UnitOfWork: Exception occurred ({exc_type.__name__}), rolling back transaction",
                    extra={"exception": str(exc_val)}
                )
                await self.rollback()
        else:
            # No exception - warn if commit wasn't called
            if not self._committed and not self._rolled_back:
                log.warning(
                    "UnitOfWork: Exiting context without explicit commit or rollback - rolling back"
                )
                await self.rollback()
        
        log.debug("UnitOfWork: Exited transaction context")
    
    async def commit(self) -> None:
        """
        Commit all changes in current transaction.
        
        Makes all repository operations within this unit of work permanent.
        Must be called explicitly before exiting context manager.
        
        Raises:
            sqlalchemy.exc.IntegrityError: If database constraints are violated
            sqlalchemy.exc.OperationalError: If database connection fails
            Exception: If already committed or rolled back
        """
        if self._committed:
            raise Exception("Transaction already committed")
        if self._rolled_back:
            raise Exception("Transaction already rolled back")
        
        try:
            await self._session.commit()
            self._committed = True
            log.info("UnitOfWork: Transaction committed successfully")
        except Exception as e:
            log.error(
                f"UnitOfWork: Commit failed, rolling back - {str(e)}",
                extra={"error_type": type(e).__name__}
            )
            await self.rollback()
            raise
    
    async def rollback(self) -> None:
        """
        Rollback all changes in current transaction.
        
        Discards all repository operations within this unit of work.
        Called automatically on exception or explicit rollback.
        """
        if self._rolled_back:
            log.debug("UnitOfWork: Already rolled back, skipping")
            return
        
        try:
            await self._session.rollback()
            self._rolled_back = True
            log.info("UnitOfWork: Transaction rolled back")
        except Exception as e:
            log.error(
                f"UnitOfWork: Rollback failed - {str(e)}",
                extra={"error_type": type(e).__name__}
            )
            raise
