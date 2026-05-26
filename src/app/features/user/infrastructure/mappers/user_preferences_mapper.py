"""
Mapper between UserPreferencesModel (infrastructure) and UserPreferencesEntity (domain).
"""

from src.app.features.user.domain.entities.user_preferences_entity import UserPreferencesEntity
from src.app.features.user.domain.value_objects.theme import Theme
from src.app.features.user.infrastructure.models.user_preferences_model import UserPreferencesModel
from src.app.shared.domain.value_objects.entity_id import EntityId


def to_entity(model: UserPreferencesModel) -> UserPreferencesEntity:
    """
    Convert UserPreferencesModel to UserPreferencesEntity.

    Args:
        model: SQLAlchemy model instance

    Returns:
        UserPreferencesEntity domain entity
    """
    return UserPreferencesEntity(
        id=EntityId(model.id),
        user_id=EntityId(model.user_id),
        theme=Theme(model.theme),
        language=model.language,
    )


def to_model(entity: UserPreferencesEntity) -> UserPreferencesModel:
    """
    Convert UserPreferencesEntity to UserPreferencesModel.

    Args:
        entity: Domain entity

    Returns:
        SQLAlchemy model instance
    """
    return UserPreferencesModel(
        id=entity.id.value,
        user_id=entity.user_id.value,
        theme=entity.theme.value,
        language=entity.language,
    )


def update_model_from_entity(model: UserPreferencesModel, entity: UserPreferencesEntity) -> UserPreferencesModel:
    """
    Update existing model with entity data.

    Args:
        model: Existing SQLAlchemy model
        entity: Domain entity with updated data

    Returns:
        Updated model instance
    """
    model.theme = entity.theme.value
    model.language = entity.language
    return model
