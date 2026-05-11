"""Mapper between ProjectModel (infrastructure) and ProjectEntity (domain)."""
from typing import Optional

from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.features.projects.infrastructure.models.project_model import ProjectModel
from src.app.shared.domain.value_objects.entity_id import EntityId


class ProjectMapper:
    """Maps between ProjectModel and ProjectEntity."""
    
    @staticmethod
    def to_entity(model: ProjectModel) -> ProjectEntity:
        """
        Convert ProjectModel to ProjectEntity.
        
        Args:
            model: SQLAlchemy ProjectModel instance
            
        Returns:
            ProjectEntity domain object
        """
        return ProjectEntity(
            id=EntityId.from_string(str(model.id)),
            name=model.name,
            description=model.description,
            created_by=EntityId.from_string(str(model.created_by)),
            status=ProjectStatus(model.status),
            start_date=model.start_date,
            end_date=model.end_date,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
    
    @staticmethod
    def to_model(entity: ProjectEntity, existing_model: Optional[ProjectModel] = None) -> ProjectModel:
        """
        Convert ProjectEntity to ProjectModel.
        
        Args:
            entity: ProjectEntity domain object
            existing_model: Optional existing model to update
            
        Returns:
            SQLAlchemy ProjectModel instance
        """
        if existing_model:
            # Update existing model
            existing_model.name = entity.name
            existing_model.description = entity.description
            existing_model.status = entity.status.value
            existing_model.start_date = entity.start_date
            existing_model.end_date = entity.end_date
            existing_model.updated_at = entity.updated_at
            return existing_model
        
        # Create new model
        return ProjectModel(
            id=entity.id.value,
            name=entity.name,
            description=entity.description,
            created_by=entity.created_by.value,
            status=entity.status.value,
            start_date=entity.start_date,
            end_date=entity.end_date,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
