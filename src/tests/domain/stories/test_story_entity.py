"""Unit tests for StoryEntity."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.shared.domain.exceptions.domain_exceptions import ValidationError
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestStoryEntityCreation:
    """Test story entity creation."""

    def test_create_story_with_required_fields(self):
        """Test creating story with only required fields."""
        project_id = EntityId.generate()
        created_by = EntityId.generate()

        with patch("src.app.features.stories.domain.entities.story_entity.datetime") as mock_datetime:
            mock_now = datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            story = StoryEntity.create(
                title="Test Story",
                project_id=project_id,
                created_by=created_by,
            )

        assert story.title == "Test Story"
        assert story.description is None
        assert story.project_id == project_id
        assert story.created_by == created_by
        assert story.assigned_to is None
        assert story.status == StoryStatus.TODO
        assert story.priority == StoryPriority.MEDIUM
        assert story.points is None
        assert story.created_at == mock_now
        assert story.updated_at == mock_now
        assert isinstance(story.id, EntityId)

    def test_create_story_with_all_fields(self):
        """Test creating story with all fields."""
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        assigned_to = EntityId.generate()

        story = StoryEntity.create(
            title="Full Story",
            project_id=project_id,
            created_by=created_by,
            description="A complete story",
            assigned_to=assigned_to,
            priority=StoryPriority.HIGH,
            points=5,
        )

        assert story.title == "Full Story"
        assert story.description == "A complete story"
        assert story.assigned_to == assigned_to
        assert story.priority == StoryPriority.HIGH
        assert story.points == 5

    def test_create_story_empty_title_raises_error(self):
        """Test creating story with empty title raises ValueError."""
        with pytest.raises(ValidationError, match="Story title cannot be empty"):
            StoryEntity.create(
                title="",
                project_id=EntityId.generate(),
                created_by=EntityId.generate(),
            )

    def test_create_story_whitespace_title_raises_error(self):
        """Test creating story with whitespace-only title raises ValueError."""
        with pytest.raises(ValidationError, match="Story title cannot be empty"):
            StoryEntity.create(
                title="   ",
                project_id=EntityId.generate(),
                created_by=EntityId.generate(),
            )

    def test_create_story_title_too_long_raises_error(self):
        """Test creating story with title > 255 chars raises ValueError."""
        long_title = "a" * 256

        with pytest.raises(ValidationError, match="Story title cannot exceed 255 characters"):
            StoryEntity.create(
                title=long_title,
                project_id=EntityId.generate(),
                created_by=EntityId.generate(),
            )

    def test_create_story_negative_points_raises_error(self):
        """Test creating story with negative points raises ValueError."""
        with pytest.raises(ValidationError, match="Story points cannot be negative"):
            StoryEntity.create(
                title="Invalid Story",
                project_id=EntityId.generate(),
                created_by=EntityId.generate(),
                points=-1,
            )

    def test_create_story_points_too_high_raises_error(self):
        """Test creating story with points > 100 raises ValueError."""
        with pytest.raises(ValidationError, match="Story points cannot exceed 100"):
            StoryEntity.create(
                title="Invalid Story",
                project_id=EntityId.generate(),
                created_by=EntityId.generate(),
                points=101,
            )


class TestStoryEntityUpdate:
    """Test story entity update operations."""

    def test_update_story_title(self):
        """Test updating story title."""
        story = StoryEntity.create(
            title="Old Title",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        with patch("src.app.shared.domain.entities.base_entity.datetime") as mock_datetime:
            mock_now = datetime(2026, 5, 10, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            story.update_details(title="New Title")

        assert story.title == "New Title"
        assert story.updated_at == mock_now

    def test_update_story_description(self):
        """Test updating story description."""
        story = StoryEntity.create(
            title="Story",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        story.update_details(description="New description")

        assert story.description == "New description"

    def test_update_story_status(self):
        """Test updating story status."""
        story = StoryEntity.create(
            title="Story",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        story.update_details(status=StoryStatus.IN_PROGRESS)

        assert story.status == StoryStatus.IN_PROGRESS

    def test_update_story_priority(self):
        """Test updating story priority."""
        story = StoryEntity.create(
            title="Story",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        story.update_details(priority=StoryPriority.HIGH)

        assert story.priority == StoryPriority.HIGH

    def test_update_story_points(self):
        """Test updating story points."""
        story = StoryEntity.create(
            title="Story",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        story.update_details(points=8)

        assert story.points == 8

    def test_update_story_empty_title_raises_error(self):
        """Test updating with empty title raises ValueError."""
        story = StoryEntity.create(
            title="Story",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        with pytest.raises(ValidationError, match="Story title cannot be empty"):
            story.update_details(title="")

    def test_update_story_invalid_points_raises_error(self):
        """Test updating with invalid points raises ValueError."""
        story = StoryEntity.create(
            title="Story",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        with pytest.raises(ValidationError, match="Story points cannot be negative"):
            story.update_details(points=-5)


class TestStoryEntityStatusTransitions:
    """Test story status transition methods."""

    def test_assign_story_to_user(self):
        """Test assigning story to a user."""
        story = StoryEntity.create(
            title="Story",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )
        user_id = EntityId.generate()

        with patch("src.app.shared.domain.entities.base_entity.datetime") as mock_datetime:
            mock_now = datetime(2026, 5, 10, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            story.assign_to(user_id)

        assert story.assigned_to == user_id
        assert story.updated_at == mock_now

    def test_unassign_story(self):
        """Test unassigning story from user."""
        story = StoryEntity.create(
            title="Story",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
            assigned_to=EntityId.generate(),
        )

        story.unassign()

        assert story.assigned_to is None

    def test_start_story(self):
        """Test starting a story."""
        story = StoryEntity.create(
            title="Story",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        with patch("src.app.shared.domain.entities.base_entity.datetime") as mock_datetime:
            mock_now = datetime(2026, 5, 10, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            story.start()

        assert story.status == StoryStatus.IN_PROGRESS
        assert story.updated_at == mock_now

    def test_complete_story(self):
        """Test completing a story."""
        story = StoryEntity.create(
            title="Story",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        with patch("src.app.shared.domain.entities.base_entity.datetime") as mock_datetime:
            mock_now = datetime(2026, 5, 10, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            story.complete()

        assert story.status == StoryStatus.DONE
        assert story.updated_at == mock_now

    def test_reopen_story(self):
        """Test reopening a completed story."""
        story = StoryEntity.create(
            title="Story",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )
        story.complete()

        with patch("src.app.shared.domain.entities.base_entity.datetime") as mock_datetime:
            mock_now = datetime(2026, 5, 10, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            story.reopen()

        assert story.status == StoryStatus.TODO
        assert story.updated_at == mock_now


class TestStoryEntityProperties:
    """Test story entity property access."""

    def test_all_properties_accessible(self):
        """Test all properties are accessible."""
        story_id = EntityId.generate()
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        assigned_to = EntityId.generate()
        now = datetime.now()

        story = StoryEntity(
            id=story_id,
            title="Test Story",
            description="Description",
            project_id=project_id,
            created_by=created_by,
            assigned_to=assigned_to,
            status=StoryStatus.IN_PROGRESS,
            priority=StoryPriority.HIGH,
            points=5,
            created_at=now,
            updated_at=now,
        )

        # Verify all properties are accessible
        assert story.id == story_id
        assert story.title == "Test Story"
        assert story.description == "Description"
        assert story.project_id == project_id
        assert story.created_by == created_by
        assert story.assigned_to == assigned_to
        assert story.status == StoryStatus.IN_PROGRESS
        assert story.priority == StoryPriority.HIGH
        assert story.points == 5
        assert story.created_at == now
        assert story.updated_at == now
