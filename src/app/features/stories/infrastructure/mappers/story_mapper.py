"""Mapper for StoryEntity and StoryModel."""

from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.features.stories.infrastructure.models.story_model import StoryModel
from src.app.shared.domain.value_objects.entity_id import EntityId


class StoryMapper:
    """Maps between StoryEntity and StoryModel."""

    @staticmethod
    def to_entity(model: StoryModel) -> StoryEntity:
        """
        Convert StoryModel to StoryEntity.

        Args:
            model: StoryModel instance

        Returns:
            StoryEntity instance
        """
        return StoryEntity(
            id=EntityId.from_string(str(model.id)),
            title=model.title,
            description=model.description,
            project_id=EntityId.from_string(str(model.project_id)),
            created_by=EntityId.from_string(str(model.created_by)),
            assigned_to=EntityId.from_string(str(model.assigned_to)) if model.assigned_to else None,
            status=StoryStatus(model.status) if isinstance(model.status, str) else model.status,
            priority=StoryPriority(model.priority) if isinstance(model.priority, str) else model.priority,
            points=model.points,
            created_at=model.created_at,
            updated_at=model.updated_at,
            acceptance_criteria=list(model.acceptance_criteria or []),
        )

    @staticmethod
    def to_model(
        entity: StoryEntity,
        existing_model: StoryModel | None = None,
    ) -> StoryModel:
        """
        Convert StoryEntity to StoryModel.

        Args:
            entity: StoryEntity instance
            existing_model: Existing model to update (optional)

        Returns:
            StoryModel instance
        """
        if existing_model:
            existing_model.title = entity.title
            existing_model.description = entity.description
            existing_model.acceptance_criteria = entity.acceptance_criteria
            existing_model.project_id = entity.project_id.value
            existing_model.created_by = entity.created_by.value
            existing_model.assigned_to = entity.assigned_to.value if entity.assigned_to else None
            existing_model.status = entity.status.value
            existing_model.priority = entity.priority.value
            existing_model.points = entity.points
            existing_model.updated_at = entity.updated_at
            return existing_model

        return StoryModel(
            id=entity.id.value,
            title=entity.title,
            description=entity.description,
            acceptance_criteria=entity.acceptance_criteria,
            project_id=entity.project_id.value,
            created_by=entity.created_by.value,
            assigned_to=entity.assigned_to.value if entity.assigned_to else None,
            status=entity.status.value,
            priority=entity.priority.value,
            points=entity.points,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
