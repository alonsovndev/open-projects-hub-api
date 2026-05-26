"""Mapper between StoryDraftModel and StoryDraftEntity."""

from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.value_objects.refinement_status import RefinementStatus
from src.app.features.refinement.infrastructure.models.story_draft_model import StoryDraftModel
from src.app.shared.domain.value_objects.entity_id import EntityId


class StoryDraftMapper:
    """Maps between StoryDraftModel and StoryDraftEntity."""

    @staticmethod
    def to_entity(model: StoryDraftModel) -> StoryDraftEntity:
        """
        Convert StoryDraftModel to StoryDraftEntity.

        Args:
            model: SQLAlchemy StoryDraftModel instance

        Returns:
            StoryDraftEntity domain object
        """
        return StoryDraftEntity(
            id=EntityId.from_string(str(model.id)),
            title=model.title,
            description=model.description,
            acceptance_criteria=model.acceptance_criteria or [],
            project_id=EntityId.from_string(str(model.project_id)),
            created_by=EntityId.from_string(str(model.created_by)),
            status=RefinementStatus(model.status),
            refined_title=model.refined_title,
            refined_description=model.refined_description,
            refined_criteria=model.refined_criteria,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: StoryDraftEntity,
        existing_model: StoryDraftModel | None = None,
    ) -> StoryDraftModel:
        """
        Convert StoryDraftEntity to StoryDraftModel.

        Args:
            entity: StoryDraftEntity domain object
            existing_model: Optional existing model to update

        Returns:
            SQLAlchemy StoryDraftModel instance
        """
        if existing_model:
            existing_model.title = entity.title
            existing_model.description = entity.description
            existing_model.acceptance_criteria = entity.acceptance_criteria
            existing_model.status = entity.status.value
            existing_model.refined_title = entity.refined_title
            existing_model.refined_description = entity.refined_description
            existing_model.refined_criteria = entity.refined_criteria
            existing_model.updated_at = entity.updated_at
            return existing_model

        return StoryDraftModel(
            id=entity.id.value,
            title=entity.title,
            description=entity.description,
            acceptance_criteria=entity.acceptance_criteria,
            project_id=entity.project_id.value,
            created_by=entity.created_by.value,
            status=entity.status.value,
            refined_title=entity.refined_title,
            refined_description=entity.refined_description,
            refined_criteria=entity.refined_criteria,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
