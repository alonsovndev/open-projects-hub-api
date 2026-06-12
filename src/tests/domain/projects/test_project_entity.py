"""Unit tests for ProjectEntity."""

from datetime import UTC, date, datetime
from unittest.mock import patch

import pytest

from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.shared.domain.exceptions.domain_exceptions import ValidationError
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestProjectEntityCreation:
    """Test project entity creation."""

    def test_create_project_with_required_fields(self):
        """Test creating project with only required fields."""
        created_by = EntityId.generate()
        client_id = EntityId.generate()

        with patch("src.app.features.projects.domain.entities.project_entity.datetime") as mock_datetime:
            mock_now = datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            project = ProjectEntity.create(
                name="Test Project",
                code="TEST",
                created_by=created_by,
                client_id=client_id,
            )

        assert project.name == "Test Project"
        assert project.code == "TEST"
        assert project.description is None
        assert project.created_by == created_by
        assert project.client_id == client_id
        assert project.status == ProjectStatus.ACTIVE
        assert project.start_date is None
        assert project.end_date is None
        assert project.created_at == mock_now
        assert project.updated_at == mock_now
        assert isinstance(project.id, EntityId)

    def test_create_project_with_all_fields(self):
        """Test creating project with all fields."""
        created_by = EntityId.generate()
        client_id = EntityId.generate()
        start = date(2026, 5, 1)
        end = date(2026, 12, 31)

        project = ProjectEntity.create(
            name="Full Project",
            code="FULL",
            created_by=created_by,
            client_id=client_id,
            description="A complete project",
            start_date=start,
            end_date=end,
        )

        assert project.name == "Full Project"
        assert project.description == "A complete project"
        assert project.start_date == start
        assert project.end_date == end

    def test_create_project_empty_name_raises_error(self):
        """Test creating project with empty name raises ValueError."""
        created_by = EntityId.generate()
        client_id = EntityId.generate()

        with pytest.raises(ValidationError, match="Project name cannot be empty"):
            ProjectEntity.create(
                name="",
                code="TEST",
                created_by=created_by,
                client_id=client_id,
            )

    def test_create_project_whitespace_name_raises_error(self):
        """Test creating project with whitespace-only name raises ValidationError."""
        created_by = EntityId.generate()
        client_id = EntityId.generate()

        with pytest.raises(ValidationError, match="Project name cannot be empty"):
            ProjectEntity.create(
                name="   ",
                code="TEST",
                created_by=created_by,
                client_id=client_id,
            )

    def test_create_project_name_too_long_raises_error(self):
        """Test creating project with name > 255 chars raises ValidationError."""
        created_by = EntityId.generate()
        client_id = EntityId.generate()
        long_name = "a" * 256

        with pytest.raises(ValidationError, match="Project name cannot exceed 255 characters"):
            ProjectEntity.create(
                name=long_name,
                code="TEST",
                created_by=created_by,
                client_id=client_id,
            )

    def test_create_project_end_before_start_raises_error(self):
        """Test creating project with end date before start date raises ValidationError."""
        created_by = EntityId.generate()
        client_id = EntityId.generate()
        start = date(2026, 12, 31)
        end = date(2026, 5, 1)

        with pytest.raises(ValidationError, match="End date cannot be before start date"):
            ProjectEntity.create(
                name="Invalid Project",
                code="TEST",
                created_by=created_by,
                client_id=client_id,
                start_date=start,
                end_date=end,
            )


class TestProjectEntityUpdate:
    """Test project entity update operations."""

    def test_update_project_name(self):
        """Test updating project name."""
        project = ProjectEntity.create(
            name="Old Name",
            code="TEST",
            created_by=EntityId.generate(),
            client_id=EntityId.generate(),
        )

        with patch("src.app.shared.domain.entities.base_entity.datetime") as mock_datetime:
            mock_now = datetime(2026, 5, 10, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            project.update_details(name="New Name")

        assert project.name == "New Name"
        assert project.updated_at == mock_now

    def test_update_project_description(self):
        """Test updating project description."""
        project = ProjectEntity.create(
            name="Project",
            code="TEST",
            created_by=EntityId.generate(),
            client_id=EntityId.generate(),
        )

        project.update_details(description="New description")

        assert project.description == "New description"

    def test_update_project_status(self):
        """Test updating project status."""
        project = ProjectEntity.create(
            name="Project",
            code="TEST",
            created_by=EntityId.generate(),
            client_id=EntityId.generate(),
        )

        project.update_details(status=ProjectStatus.COMPLETED)

        assert project.status == ProjectStatus.COMPLETED

    def test_update_project_dates(self):
        """Test updating project start and end dates."""
        project = ProjectEntity.create(
            name="Project",
            code="TEST",
            created_by=EntityId.generate(),
            client_id=EntityId.generate(),
        )

        new_start = date(2026, 6, 1)
        new_end = date(2026, 12, 31)

        project.update_details(start_date=new_start, end_date=new_end)

        assert project.start_date == new_start
        assert project.end_date == new_end

    def test_update_project_empty_name_raises_error(self):
        """Test updating with empty name raises ValidationError."""
        project = ProjectEntity.create(
            name="Project",
            code="TEST",
            created_by=EntityId.generate(),
            client_id=EntityId.generate(),
        )

        with pytest.raises(ValidationError, match="Project name cannot be empty"):
            project.update_details(name="")

    def test_update_project_invalid_dates_raises_error(self):
        """Test updating with invalid dates raises ValidationError."""
        project = ProjectEntity.create(
            name="Project",
            code="TEST",
            created_by=EntityId.generate(),
            client_id=EntityId.generate(),
            start_date=date(2026, 5, 1),
        )

        with pytest.raises(ValidationError, match="End date cannot be before start date"):
            project.update_details(end_date=date(2026, 4, 1))


class TestProjectEntityStatusTransitions:
    """Test project status transition methods."""

    def test_archive_project(self):
        """Test archiving a project."""
        project = ProjectEntity.create(
            name="Project",
            code="TEST",
            created_by=EntityId.generate(),
            client_id=EntityId.generate(),
        )

        with patch("src.app.shared.domain.entities.base_entity.datetime") as mock_datetime:
            mock_now = datetime(2026, 5, 10, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            project.archive()

        assert project.status == ProjectStatus.ARCHIVED
        assert project.updated_at == mock_now

    def test_complete_project(self):
        """Test completing a project."""
        project = ProjectEntity.create(
            name="Project",
            code="TEST",
            created_by=EntityId.generate(),
            client_id=EntityId.generate(),
        )

        with patch("src.app.shared.domain.entities.base_entity.datetime") as mock_datetime:
            mock_now = datetime(2026, 5, 10, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            project.complete()

        assert project.status == ProjectStatus.COMPLETED
        assert project.updated_at == mock_now

    def test_reactivate_archived_project(self):
        """Test reactivating an archived project."""
        project = ProjectEntity.create(
            name="Project",
            code="TEST",
            created_by=EntityId.generate(),
            client_id=EntityId.generate(),
        )
        project.archive()

        with patch("src.app.shared.domain.entities.base_entity.datetime") as mock_datetime:
            mock_now = datetime(2026, 5, 10, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            project.reactivate()

        assert project.status == ProjectStatus.ACTIVE
        assert project.updated_at == mock_now

    def test_reactivate_completed_project(self):
        """Test reactivating a completed project."""
        project = ProjectEntity.create(
            name="Project",
            code="TEST",
            created_by=EntityId.generate(),
            client_id=EntityId.generate(),
        )
        project.complete()

        project.reactivate()

        assert project.status == ProjectStatus.ACTIVE


class TestProjectEntityProperties:
    """Test project entity property access."""

    def test_all_properties_accessible(self):
        """Test all properties are accessible."""
        from src.app.features.projects.domain.value_objects.project_priority import ProjectPriority

        project_id = EntityId.generate()
        created_by = EntityId.generate()
        client_id = EntityId.generate()
        start = date(2026, 5, 1)
        end = date(2026, 12, 31)
        now = datetime.now()

        project = ProjectEntity(
            id=project_id,
            name="Test Project",
            code="TEST",
            description="Description",
            created_by=created_by,
            client_id=client_id,
            status=ProjectStatus.ACTIVE,
            priority=ProjectPriority.MEDIUM,
            start_date=start,
            end_date=end,
            created_at=now,
            updated_at=now,
        )

        # Verify all properties are accessible
        assert project.id == project_id
        assert project.name == "Test Project"
        assert project.code == "TEST"
        assert project.description == "Description"
        assert project.created_by == created_by
        assert project.client_id == client_id
        assert project.status == ProjectStatus.ACTIVE
        assert project.priority == ProjectPriority.MEDIUM
        assert project.start_date == start
        assert project.end_date == end
        assert project.created_at == now
        assert project.updated_at == now
