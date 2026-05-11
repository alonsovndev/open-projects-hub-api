"""Story repository implementation using SQLAlchemy."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.stories.infrastructure.mappers.story_mapper import StoryMapper
from src.app.features.stories.infrastructure.models.story_model import StoryModel
from src.app.shared.utils.log_util import log


class StoryRepositoryImpl(StoryRepository):
    """SQLAlchemy implementation of StoryRepository."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self._session = session
    
    async def find_by_id(self, story_id: UUID) -> Optional[StoryEntity]:
        """
        Find story by ID.
        
        Args:
            story_id: Story UUID
            
        Returns:
            StoryEntity if found, None otherwise
            
        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(StoryModel).where(StoryModel.id == story_id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                return StoryMapper.to_entity(model)
            return None
        
        except OperationalError as e:
            log.error(
                f"Database connection error while fetching story {story_id}: {e}",
                exc_info=True
            )
            raise
        except SQLAlchemyError as e:
            log.error(
                f"Database error while fetching story {story_id}: {e}",
                exc_info=True
            )
            raise
    
    async def find_all(
        self,
        limit: int = 20,
        offset: int = 0,
        project_id: Optional[UUID] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
    ) -> List[StoryEntity]:
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
            
        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(StoryModel)
            
            if project_id:
                stmt = stmt.where(StoryModel.project_id == project_id)
            if status:
                stmt = stmt.where(StoryModel.status == status)
            if priority:
                stmt = stmt.where(StoryModel.priority == priority)
            if assigned_to:
                stmt = stmt.where(StoryModel.assigned_to == assigned_to)
            
            stmt = stmt.order_by(StoryModel.created_at.desc())
            stmt = stmt.limit(limit).offset(offset)
            
            result = await self._session.execute(stmt)
            models = result.scalars().all()
            
            return [StoryMapper.to_entity(model) for model in models]
        
        except OperationalError as e:
            log.error(
                f"Database connection error while fetching stories: {e}",
                exc_info=True
            )
            raise
        except SQLAlchemyError as e:
            log.error(
                f"Database error while fetching stories: {e}",
                exc_info=True
            )
            raise
    
    async def find_by_project_id(
        self,
        project_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> List[StoryEntity]:
        """
        Find all stories for a specific project.
        
        Args:
            project_id: Project UUID
            limit: Maximum number of results (default 20)
            offset: Number of results to skip (default 0)
            
        Returns:
            List of StoryEntity objects
        """
        return await self.find_all(limit=limit, offset=offset, project_id=project_id)
    
    async def find_by_assigned_user(self, user_id: UUID) -> List[StoryEntity]:
        """
        Find all stories assigned to a specific user.
        
        Args:
            user_id: User UUID
            
        Returns:
            List of StoryEntity objects
        """
        return await self.find_all(assigned_to=user_id)
    
    async def save(self, story: StoryEntity) -> Optional[StoryEntity]:
        """
        Save or update a story.
        
        Args:
            story: StoryEntity to save
            
        Returns:
            Saved StoryEntity if successful
            
        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            # Check if story exists
            stmt = select(StoryModel).where(StoryModel.id == story.id.value)
            result = await self._session.execute(stmt)
            existing_model = result.scalar_one_or_none()
            
            # Convert entity to model (update existing or create new)
            model = StoryMapper.to_model(story, existing_model)
            
            if not existing_model:
                self._session.add(model)
            
            await self._session.commit()
            await self._session.refresh(model)
            
            return StoryMapper.to_entity(model)
        
        except OperationalError as e:
            await self._session.rollback()
            log.error(
                f"Database connection error while saving story {story.id.value}: {e}",
                exc_info=True
            )
            raise
        except SQLAlchemyError as e:
            await self._session.rollback()
            log.error(
                f"Database error while saving story {story.id.value}: {e}",
                exc_info=True
            )
            raise
    
    async def delete(self, story_id: UUID) -> bool:
        """
        Delete a story by ID.
        
        Args:
            story_id: Story UUID
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(StoryModel).where(StoryModel.id == story_id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return False
            
            await self._session.delete(model)
            await self._session.commit()
            
            return True
        
        except OperationalError as e:
            await self._session.rollback()
            log.error(
                f"Database connection error while deleting story {story_id}: {e}",
                exc_info=True
            )
            raise
        except SQLAlchemyError as e:
            await self._session.rollback()
            log.error(
                f"Database error while deleting story {story_id}: {e}",
                exc_info=True
            )
            raise
    
    async def exists(self, story_id: UUID) -> bool:
        """
        Check if a story exists by ID.
        
        Args:
            story_id: Story UUID
            
        Returns:
            True if story exists, False otherwise
            
        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(func.count(StoryModel.id)).where(StoryModel.id == story_id)
            result = await self._session.execute(stmt)
            count = result.scalar_one()
            
            return count > 0
        
        except OperationalError as e:
            log.error(
                f"Database connection error while checking story existence {story_id}: {e}",
                exc_info=True
            )
            raise
        except SQLAlchemyError as e:
            log.error(
                f"Database error while checking story existence {story_id}: {e}",
                exc_info=True
            )
            raise
    
    async def update(self, story: StoryEntity) -> Optional[StoryEntity]:
        """
        Update an existing story.
        
        Args:
            story: StoryEntity to update
            
        Returns:
            Updated StoryEntity if successful, None if not found
            
        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            # Check if story exists
            stmt = select(StoryModel).where(StoryModel.id == story.id.value)
            result = await self._session.execute(stmt)
            existing_model = result.scalar_one_or_none()
            
            if not existing_model:
                log.warning(f"Story {story.id.value} not found for update")
                return None
            
            # Convert entity to model (update existing)
            model = StoryMapper.to_model(story, existing_model)
            
            await self._session.commit()
            await self._session.refresh(model)
            
            return StoryMapper.to_entity(model)
        
        except OperationalError as e:
            await self._session.rollback()
            log.error(
                f"Database connection error while updating story {story.id.value}: {e}",
                exc_info=True
            )
            raise
        except SQLAlchemyError as e:
            await self._session.rollback()
            log.error(
                f"Database error while updating story {story.id.value}: {e}",
                exc_info=True
            )
            raise
    
    async def count(
        self,
        project_id: Optional[UUID] = None,
        status: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
    ) -> int:
        """
        Count stories with optional filters.
        
        Args:
            project_id: Optional project filter
            status: Optional status filter
            assigned_to: Optional assigned user filter
            
        Returns:
            Number of stories matching filters
            
        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(func.count(StoryModel.id))
            
            if project_id:
                stmt = stmt.where(StoryModel.project_id == project_id)
            if status:
                stmt = stmt.where(StoryModel.status == status)
            if assigned_to:
                stmt = stmt.where(StoryModel.assigned_to == assigned_to)
            
            result = await self._session.execute(stmt)
            count = result.scalar_one()
            
            return count
        
        except OperationalError as e:
            log.error(
                f"Database connection error while counting stories: {e}",
                exc_info=True
            )
            raise
        except SQLAlchemyError as e:
            log.error(
                f"Database error while counting stories: {e}",
                exc_info=True
            )
            raise