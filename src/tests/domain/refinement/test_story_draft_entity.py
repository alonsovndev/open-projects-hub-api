"""Unit tests for StoryDraftEntity."""
from datetime import datetime
from unittest.mock import patch

import pytest

from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.value_objects.refinement_status import RefinementStatus
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestStoryDraftEntityCreation:
    """Test story draft entity creation."""

    def test_create_draft_with_required_fields(self):
        """Test creating draft with only required fields."""
        project_id = EntityId.generate()
        created_by = EntityId.generate()

        with patch("src.app.features.refinement.domain.entities.story_draft_entity.datetime") as mock_datetime:
            mock_now = datetime(2026, 5, 21, 12, 0, 0)
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
        assert draft.status == RefinementStatus.DRAFT
        assert draft.refined_title is None
        assert draft.refined_description is None
        assert draft.refined_criteria is None
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
        """Test creating draft with empty title raises ValueError."""
        with pytest.raises(ValueError, match="Story title cannot be empty"):
            StoryDraftEntity.create(
                title="",
                project_id=EntityId.generate(),
                created_by=EntityId.generate(),
            )

    def test_create_draft_whitespace_title_raises_error(self):
        """Test creating draft with whitespace-only title raises ValueError."""
        with pytest.raises(ValueError, match="Story title cannot be empty"):
            StoryDraftEntity.create(
                title="   ",
                project_id=EntityId.generate(),
                created_by=EntityId.generate(),
            )

    def test_create_draft_title_too_long_raises_error(self):
        """Test creating draft with title > 500 chars raises ValueError."""
        long_title = "a" * 501

        with pytest.raises(ValueError, match="Story title cannot exceed 500 characters"):
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
            mock_now = datetime(2026, 5, 22, 12, 0, 0)
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
        """Test updating with empty title raises ValueError."""
        draft = StoryDraftEntity.create(
            title="Draft",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        with pytest.raises(ValueError, match="Story title cannot be empty"):
            draft.update_draft(title="")

    def test_update_draft_title_too_long_raises_error(self):
        """Test updating with title > 500 chars raises ValueError."""
        draft = StoryDraftEntity.create(
            title="Draft",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        long_title = "a" * 501

        with pytest.raises(ValueError, match="Story title cannot exceed 500 characters"):
            draft.update_draft(title=long_title)

    def test_update_draft_resets_refined_status(self):
        """Test updating draft resets status from REFINED to DRAFT."""
        draft = StoryDraftEntity.create(
            title="Draft",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        draft.start_refinement()
        draft.apply_refinement(
            refined_title="Refined Title",
            refined_description="Refined description",
            refined_criteria=["Refined criterion"],
        )

        assert draft.status == RefinementStatus.REFINED
        assert draft.refined_title == "Refined Title"

        draft.update_draft(title="Updated Title")

        assert draft.status == RefinementStatus.DRAFT
        assert draft.refined_title is None
        assert draft.refined_description is None
        assert draft.refined_criteria is None

    def test_update_draft_does_not_affect_draft_status(self):
        """Test updating draft does not change DRAFT status."""
        draft = StoryDraftEntity.create(
            title="Draft",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        draft.update_draft(title="Updated Title")

        assert draft.status == RefinementStatus.DRAFT

    def test_update_draft_does_not_affect_refining_status(self):
        """Test updating draft does not change REFINING status."""
        draft = StoryDraftEntity.create(
            title="Draft",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        draft.start_refinement()

        draft.update_draft(title="Updated Title")

        assert draft.status == RefinementStatus.REFINING


class TestStoryDraftEntityRefinement:
    """Test story draft refinement lifecycle."""

    def test_start_refinement(self):
        """Test starting refinement changes status to REFINING."""
        draft = StoryDraftEntity.create(
            title="Draft",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        with patch("src.app.shared.domain.entities.base_entity.datetime") as mock_datetime:
            mock_now = datetime(2026, 5, 22, 12, 0, 0)
            mock_datetime.now.return_value = mock_now

            draft.start_refinement()

        assert draft.status == RefinementStatus.REFINING
        assert draft.updated_at == mock_now

    def test_apply_refinement(self):
        """Test applying refinement changes status to REFINED."""
        draft = StoryDraftEntity.create(
            title="Draft",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        draft.start_refinement()

        with patch("src.app.shared.domain.entities.base_entity.datetime") as mock_datetime:
            mock_now = datetime(2026, 5, 22, 12, 0, 0)
            mock_datetime.now.return_value = mock_now

            draft.apply_refinement(
                refined_title="Refined Title",
                refined_description="Refined description",
                refined_criteria=["Refined criterion"],
            )

        assert draft.status == RefinementStatus.REFINED
        assert draft.refined_title == "Refined Title"
        assert draft.refined_description == "Refined description"
        assert draft.refined_criteria == ["Refined criterion"]
        assert draft.updated_at == mock_now

    def test_apply_refinement_with_only_title(self):
        """Test applying refinement with only title."""
        draft = StoryDraftEntity.create(
            title="Draft",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        draft.apply_refinement(refined_title="Refined Title")

        assert draft.status == RefinementStatus.REFINED
        assert draft.refined_title == "Refined Title"
        assert draft.refined_description is None
        assert draft.refined_criteria is None

    def test_mark_applied(self):
        """Test marking draft as applied changes status to APPLIED."""
        draft = StoryDraftEntity.create(
            title="Draft",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
        )

        draft.start_refinement()
        draft.apply_refinement(refined_title="Refined Title")

        with patch("src.app.shared.domain.entities.base_entity.datetime") as mock_datetime:
            mock_now = datetime(2026, 5, 22, 12, 0, 0)
            mock_datetime.now.return_value = mock_now

            draft.mark_applied()

        assert draft.status == RefinementStatus.APPLIED
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
            status=RefinementStatus.REFINED,
            refined_title="Refined Title",
            refined_description="Refined description",
            refined_criteria=["Refined criterion"],
            created_at=now,
            updated_at=now,
        )

        assert draft.id == draft_id
        assert draft.title == "Test Draft"
        assert draft.description == "Description"
        assert draft.acceptance_criteria == ["Criterion 1"]
        assert draft.project_id == project_id
        assert draft.created_by == created_by
        assert draft.status == RefinementStatus.REFINED
        assert draft.refined_title == "Refined Title"
        assert draft.refined_description == "Refined description"
        assert draft.refined_criteria == ["Refined criterion"]
        assert draft.created_at == now
        assert draft.updated_at == now
