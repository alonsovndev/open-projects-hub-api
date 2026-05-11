"""Project repository implementation using SQLAlchemy."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.projects.infrastructure.mappers.project_mapper import ProjectMapper
from src.app.features.projects.infrastructure.models.project_model import ProjectModel
from src.app.shared.utils.log_util import log


class ProjectRepositoryImpl(ProjectRepository):
    """SQLAlchemy implementation of ProjectRepository."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self._session = session
    
    async def find_by_id(self, project_id: UUID) -> Optional[ProjectEntity]:
        """
        Find project by ID.
        
        Args:
            project_id: Project UUID
            
        Returns:
            ProjectEntity if found, None otherwise
            
        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(ProjectModel).where(ProjectModel.id == project_id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                return ProjectMapper.to_entity(model)
            return None
        
        except OperationalError as e:
            log.error(
                f"Database connection error while fetching project {project_id}: {e}",
                exc_info=True
            )
            raise
        except SQLAlchemyError as e:
            log.error(
                f"Database error while fetching project {project_id}: {e}",
                exc_info=True
            )
            raise
    
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
            
        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(ProjectModel)
            
            if status:
                stmt = stmt.where(ProjectModel.status == status)
            
            stmt = stmt.order_by(ProjectModel.created_at.desc())
            stmt = stmt.limit(limit).offset(offset)
            
            result = await self._session.execute(stmt)
            models = result.scalars().all()
            
            return [ProjectMapper.to_entity(model) for model in models]
        
        except OperationalError as e:
            log.error(
                f"Database connection error while fetching projects: {e}",
                exc_info=True
            )
            raise
        except SQLAlchemyError as e:
            log.error(
                f"Database error while fetching projects: {e}",
                exc_info=True
            )
            raise
    
    async def save(self, project: ProjectEntity) -> Optional[ProjectEntity]:
        """
        Save or update a project.
        
        Args:
            project: ProjectEntity to save
            
        Returns:
            Saved ProjectEntity if successful
            
        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            # Check if project exists
            stmt = select(ProjectModel).where(ProjectModel.id == project.id.value)
            result = await self._session.execute(stmt)
            existing_model = result.scalar_one_or_none()
            
            # Convert entity to model (update existing or create new)
            model = ProjectMapper.to_model(project, existing_model)
            
            if not existing_model:
                self._session.add(model)
            
            await self._session.commit()
            await self._session.refresh(model)
            
            return ProjectMapper.to_entity(model)
        
        except OperationalError as e:
            await self._session.rollback()
            log.error(
                f"Database connection error while saving project {project.id.value}: {e}",
                exc_info=True
            )
            raise
        except SQLAlchemyError as e:
            await self._session.rollback()
            log.error(
                f"Database error while saving project {project.id.value}: {e}",
                exc_info=True
            )
            raise
    
    async def delete(self, project_id: UUID) -> bool:
        """
        Delete a project by ID.
        
        Args:
            project_id: Project UUID
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(ProjectModel).where(ProjectModel.id == project_id)
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
                f"Database connection error while deleting project {project_id}: {e}",
                exc_info=True
            )
            raise
        except SQLAlchemyError as e:
            await self._session.rollback()
            log.error(
                f"Database error while deleting project {project_id}: {e}",
                exc_info=True
            )
            raise
    
    async def exists(self, project_id: UUID) -> bool:
        """
        Check if a project exists by ID.
        
        Args:
            project_id: Project UUID
            
        Returns:
            True if project exists, False otherwise
            
        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(func.count(ProjectModel.id)).where(ProjectModel.id == project_id)
            result = await self._session.execute(stmt)
            count = result.scalar_one()
            
            return count > 0
        
        except OperationalError as e:
            log.error(
                f"Database connection error while checking project existence {project_id}: {e}",
                exc_info=True
            )
            raise
        except SQLAlchemyError as e:
            log.error(
                f"Database error while checking project existence {project_id}: {e}",
                exc_info=True
            )
            raise
    
    async def update(self, project: ProjectEntity) -> Optional[ProjectEntity]:
        """
        Update an existing project.
        
        Args:
            project: ProjectEntity to update
            
        Returns:
            Updated ProjectEntity if successful, None if not found
            
        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            # Check if project exists
            stmt = select(ProjectModel).where(ProjectModel.id == project.id.value)
            result = await self._session.execute(stmt)
            existing_model = result.scalar_one_or_none()
            
            if not existing_model:
                log.warning(f"Project {project.id.value} not found for update")
                return None
            
            # Convert entity to model (update existing)
            model = ProjectMapper.to_model(project, existing_model)
            
            await self._session.commit()
            await self._session.refresh(model)
            
            return ProjectMapper.to_entity(model)
        
        except OperationalError as e:
            await self._session.rollback()
            log.error(
                f"Database connection error while updating project {project.id.value}: {e}",
                exc_info=True
            )
            raise
        except SQLAlchemyError as e:
            await self._session.rollback()
            log.error(
                f"Database error while updating project {project.id.value}: {e}",
                exc_info=True
            )
            raise
    
    async def count(self, status: Optional[str] = None) -> int:
        """
        Count projects with optional status filter.
        
        Args:
            status: Optional status filter
            
        Returns:
            Number of projects
            
        Raises:
            SQLAlchemyError: If database error occurs
        """
        try:
            stmt = select(func.count(ProjectModel.id))
            
            if status:
                stmt = stmt.where(ProjectModel.status == status)
            
            result = await self._session.execute(stmt)
            count = result.scalar_one()
            
            return count
        
        except OperationalError as e:
            log.error(
                f"Database connection error while counting projects: {e}",
                exc_info=True
            )
            raise
        except SQLAlchemyError as e:
            log.error(
                f"Database error while counting projects: {e}",
                exc_info=True
            )
            raise
