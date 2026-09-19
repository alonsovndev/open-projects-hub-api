"""Unit tests for StoryDraftEntity."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.value_objects.draft_status import DraftStatus
from src.app.shared.domain.exceptions.domain_exceptions import ValidationError
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestStoryDraftEntityCreation:
    """Test story draft entity creation."""

    def test_create_draft_with_required_fields(self):
        """Test creating draft with only required fields."""
        project_id = EntityId.generate()
        created_by = EntityId.generate()

        with patch("src.app.features.refinement.domain.entities.story_draft_entity.datetime") as mock_datetime:
            mock_now = datetime(2026, 5, 21, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            draft = StoryDraftEntity.create(
                title="Test Draft",
                project_id=project_id,
                created_by=created_by,
            )

        assert draft.title == "Test Draft"
        assert draft.description is None
        assert draft.acceptance_criteria == []
        assert draft.project_id == project_id
        assert draft.created_by == created_by
        assert draft.status == DraftStatus.DRAFT
        assert draft.created_at == mock_now
        assert draft.updated_at == mock_now
        assert isinstance(draft.id, EntityId)

    def test_create_draft_with_all_fields(self):
        """Test creating draft with all optional fields."""
        project_id = EntityId.generate()
        created_by = EntityId.generate()

        draft = StoryDraftEntity.create(
            title="Full Draft",
            project_id=project_id,
            created_by=created_by,
            description="A complete draft",
            acceptance_criteria=["Criterion 1", "Criterion 2"],
        )

        assert draft.title == "Full Draft"
        assert draft.description == "A complete draft"
        assert draft.acceptance_criteria == ["Criterion 1", "Criterion 2"]

    def test_create_draft_empty_title_raises_error(self):
        """Test creating draft with empty title raises ValidationError."""
        with pytest.raises(ValidationError, match="Story title cannot be empty"):
            StoryDraftEntity.create(
                title="",
                project_id=EntityId.generate(),
                created_by=EntityId.generate(),
            )

    def test_create_draft_whitespace_title_raises_error(self):
        """Test creating draft with whitespace-only title raises ValidationError."""
        with pytest.raises(ValidationError, match="Story title cannot be empty"):
            StoryDraftEntity.create(
                title="   ",
                project_id=EntityId.generate(),
                created_by=EntityId.generate(),
            )

    def test_create_draft_title_too_long_raises_error(self):
        """Test creating draft with title > 500 chars raises ValidationError."""
        long_title = "a" * 501

        with pytest.raises(ValidationError, match="Story title cannot exceed 500 characters"):
            StoryDraftEntity.create(
                title=long_title,
                project_id=EntityId.generate(),
                created_by=EntityId.generate(),
            )

    def test_create_draft_title_at_max_length_succeeds(self):
        """Test creating draft with title at exactly 500 chars succeeds."""
        max_title = "a" * 500

        draft = StoryDraftEntity.create(
            title=max_title,
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        assert draft.title == max_title


class TestStoryDraftEntityUpdate:
    """Test story draft entity update operations."""

    def test_update_draft_title(self):
        """Test updating draft title."""
        draft = StoryDraftEntity.create(
            title="Old Title",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        with patch("src.app.shared.domain.entities.base_entity.datetime") as mock_datetime:
            mock_now = datetime(2026, 5, 22, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            draft.update_draft(title="New Title")

        assert draft.title == "New Title"
        assert draft.updated_at == mock_now

    def test_update_draft_description(self):
        """Test updating draft description."""
        draft = StoryDraftEntity.create(
            title="Draft",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        draft.update_draft(description="New description")

        assert draft.description == "New description"

    def test_update_draft_acceptance_criteria(self):
        """Test updating draft acceptance criteria."""
        draft = StoryDraftEntity.create(
            title="Draft",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        draft.update_draft(acceptance_criteria=["New criterion"])

        assert draft.acceptance_criteria == ["New criterion"]

    def test_update_draft_empty_title_raises_error(self):
        """Test updating with empty title raises ValidationError."""
        draft = StoryDraftEntity.create(
            title="Draft",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        with pytest.raises(ValidationError, match="Story title cannot be empty"):
            draft.update_draft(title="")

    def test_update_draft_title_too_long_raises_error(self):
        """Test updating with title > 500 chars raises ValidationError."""
        draft = StoryDraftEntity.create(
            title="Draft",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        long_title = "a" * 501

        with pytest.raises(ValidationError, match="Story title cannot exceed 500 characters"):
            draft.update_draft(title=long_title)

    def test_update_draft_preserves_draft_status(self):
        """Test updating a draft keeps it in DRAFT status."""
        draft = StoryDraftEntity.create(
            title="Draft",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        draft.update_draft(title="Updated Title")

        assert draft.status == DraftStatus.DRAFT

    def test_update_draft_partial_fields(self):
        """Test updating only some fields leaves others unchanged."""
        draft = StoryDraftEntity.create(
            title="Original Title",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
            description="Original description",
            acceptance_criteria=["Original criterion"],
        )

        draft.update_draft(title="Updated Title")

        assert draft.title == "Updated Title"
        assert draft.description == "Original description"
        assert draft.acceptance_criteria == ["Original criterion"]


class TestStoryDraftEntityLifecycle:
    """Test story draft lifecycle (DRAFT → APPLIED)."""

    def test_mark_applied(self):
        """Test marking draft as applied changes status to APPLIED."""
        draft = StoryDraftEntity.create(
            title="Draft",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        with patch("src.app.shared.domain.entities.base_entity.datetime") as mock_datetime:
            mock_now = datetime(2026, 5, 22, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            draft.mark_applied()

        assert draft.status == DraftStatus.APPLIED
        assert draft.updated_at == mock_now


class TestStoryDraftEntityProperties:
    """Test story draft entity property access."""

    def test_all_properties_accessible(self):
        """Test all properties are accessible."""
        draft_id = EntityId.generate()
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        now = datetime.now()

        draft = StoryDraftEntity(
            id=draft_id,
            title="Test Draft",
            description="Description",
            acceptance_criteria=["Criterion 1"],
            project_id=project_id,
            created_by=created_by,
            status=DraftStatus.DRAFT,
            created_at=now,
            updated_at=now,
        )

        assert draft.id == draft_id
        assert draft.title == "Test Draft"
        assert draft.description == "Description"
        assert draft.acceptance_criteria == ["Criterion 1"]
        assert draft.project_id == project_id
        assert draft.created_by == created_by
        assert draft.status == DraftStatus.DRAFT
        assert draft.created_at == now
        assert draft.updated_at == now
