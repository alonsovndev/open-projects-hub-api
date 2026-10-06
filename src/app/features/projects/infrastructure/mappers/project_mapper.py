"""Mapper between ProjectModel (infrastructure) and ProjectEntity (domain)."""

from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.value_objects.project_phase import ProjectPhase
from src.app.features.projects.domain.value_objects.project_priority import ProjectPriority
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
            code=model.code,
            description=model.description,
            created_by=EntityId.from_string(str(model.created_by)),
            client_id=EntityId.from_string(str(model.client_id)),
            status=ProjectStatus(model.status),
            priority=ProjectPriority(model.priority),
            start_date=model.start_date,
            end_date=model.end_date,
            created_at=model.created_at,
            updated_at=model.updated_at,
            phase=ProjectPhase(model.phase),
            workspace_id=EntityId.from_string(str(model.workspace_id)) if model.workspace_id else None,
            access_code=model.access_code,
        )

    @staticmethod
    def to_model(entity: ProjectEntity, existing_model: ProjectModel | None = None) -> ProjectModel:
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
            existing_model.code = entity.code
            existing_model.description = entity.description
            existing_model.client_id = entity.client_id.value
            existing_model.status = entity.status.value
            existing_model.priority = entity.priority.value
            existing_model.phase = entity.phase.value
            existing_model.access_code = entity.access_code
            existing_model.start_date = entity.start_date
            existing_model.end_date = entity.end_date
            existing_model.updated_at = entity.updated_at
            return existing_model

        # Create new model
        return ProjectModel(
            id=entity.id.value,
            name=entity.name,
            code=entity.code,
            description=entity.description,
            created_by=entity.created_by.value,
            client_id=entity.client_id.value,
            status=entity.status.value,
            priority=entity.priority.value,
            phase=entity.phase.value,
            workspace_id=entity.workspace_id.value if entity.workspace_id else None,
            access_code=entity.access_code,
            start_date=entity.start_date,
            end_date=entity.end_date,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
