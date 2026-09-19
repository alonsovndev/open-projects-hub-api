"""Unit tests for StoryMapper."""

from datetime import datetime
from unittest.mock import MagicMock

from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.features.stories.infrastructure.mappers.story_mapper import StoryMapper
from src.app.features.stories.infrastructure.models.story_model import StoryModel
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestStoryMapperToEntity:
    """Test StoryMapper.to_entity method."""

    def test_to_entity_with_all_fields(self):
        """Test converting model with all fields to entity."""
        model_id = "550e8400-e29b-41d4-a716-446655440100"
        project_id = "550e8400-e29b-41d4-a716-446655440101"
        created_by = "550e8400-e29b-41d4-a716-446655440102"
        assigned_to = "550e8400-e29b-41d4-a716-446655440103"
        now = datetime.now()

        model = MagicMock(spec=StoryModel)
        model.id = model_id
        model.title = "Test Story"
        model.description = "Test description"
        model.project_id = project_id
        model.created_by = created_by
        model.assigned_to = assigned_to
        model.status = "in_progress"
        model.priority = "high"
        model.points = 5
        model.created_at = now
        model.updated_at = now

        entity = StoryMapper.to_entity(model)

        assert str(entity.id.value) == model_id
        assert entity.title == "Test Story"
        assert entity.description == "Test description"
        assert str(entity.project_id.value) == project_id
        assert str(entity.created_by.value) == created_by
        assert str(entity.assigned_to.value) == assigned_to
        assert entity.status == StoryStatus.IN_PROGRESS
        assert entity.priority == StoryPriority.HIGH
        assert entity.points == 5
        assert entity.created_at == now
        assert entity.updated_at == now

    def test_to_entity_with_null_optional_fields(self):
        """Test converting model with null optional fields to entity."""
        model_id = "550e8400-e29b-41d4-a716-446655440100"
        project_id = "550e8400-e29b-41d4-a716-446655440101"
        created_by = "550e8400-e29b-41d4-a716-446655440102"
        now = datetime.now()

        model = MagicMock(spec=StoryModel)
        model.id = model_id
        model.title = "Test Story"
        model.description = None
        model.project_id = project_id
        model.created_by = created_by
        model.assigned_to = None
        model.status = "todo"
        model.priority = "medium"
        model.points = None
        model.created_at = now
        model.updated_at = now

        entity = StoryMapper.to_entity(model)

        assert entity.description is None
        assert entity.assigned_to is None
        assert entity.points is None
        assert entity.status == StoryStatus.TODO
        assert entity.priority == StoryPriority.MEDIUM


class TestStoryMapperToModel:
    """Test StoryMapper.to_model method."""

    def test_to_model_creates_new_model(self):
        """Test creating new model from entity."""
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        now = datetime.now()

        entity = StoryEntity(
            id=EntityId.generate(),
            title="Test Story",
            description="Test description",
            project_id=project_id,
            created_by=created_by,
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.MEDIUM,
            points=3,
            created_at=now,
            updated_at=now,
        )

        model = StoryMapper.to_model(entity)

        assert model.id == entity.id.value
        assert model.title == "Test Story"
        assert model.description == "Test description"
        assert model.project_id == project_id.value
        assert model.created_by == created_by.value
        assert model.assigned_to is None
        assert model.status == "todo"
        assert model.priority == "medium"
        assert model.points == 3

    def test_to_model_updates_existing_model(self):
        """Test updating existing model from entity."""
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        new_project_id = EntityId.generate()
        now = datetime.now()

        entity = StoryEntity(
            id=EntityId.generate(),
            title="Updated Title",
            description="Updated description",
            project_id=new_project_id,
            created_by=created_by,
            assigned_to=None,
            status=StoryStatus.DONE,
            priority=StoryPriority.HIGH,
            points=8,
            created_at=now,
            updated_at=now,
        )

        # Create mock existing model
        existing_model = MagicMock(spec=StoryModel)
        existing_model.id = entity.id.value
        existing_model.title = "Old Title"
        existing_model.description = "Old description"
        existing_model.project_id = project_id.value
        existing_model.created_by = created_by.value
        existing_model.assigned_to = None
        existing_model.status = "todo"
        existing_model.priority = "low"
        existing_model.points = 1
        existing_model.created_at = now
        existing_model.updated_at = now

        updated_model = StoryMapper.to_model(entity, existing_model)

        assert updated_model == existing_model
        assert existing_model.title == "Updated Title"
        assert existing_model.description == "Updated description"
        assert existing_model.project_id == new_project_id.value
        assert existing_model.status == "done"
        assert existing_model.priority == "high"
        assert existing_model.points == 8
