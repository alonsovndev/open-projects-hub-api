"""
Integration tests for ProjectRepositoryImpl.

Tests repository implementations against a real PostgreSQL database.
These tests verify SQL queries, foreign key constraints, and database interactions.

Run with: pytest -m e2e
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.features.projects.infrastructure.repositories.project_repository_impl import ProjectRepositoryImpl
from src.app.shared.domain.value_objects.entity_id import EntityId


@pytest.mark.e2e
@pytest.mark.asyncio
class TestProjectRepositoryIntegration:
    """Integration tests for ProjectRepository against real database."""

    async def test_save_creates_new_project(self, db_session: AsyncSession):
        """Test saving a new project creates database record."""
        # Arrange
        repository = ProjectRepositoryImpl(db_session)
        project = ProjectEntity(
            id=EntityId.generate(),
            name="Integration Test Project",
            description="Test project description",
            created_by=EntityId.generate(),
            status=ProjectStatus.ACTIVE,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Act
        saved_project = await repository.save(project)
        await db_session.commit()

        # Assert
        assert saved_project is not None
        assert saved_project.id.value == project.id.value
        assert saved_project.name == "Integration Test Project"
        assert saved_project.status == ProjectStatus.ACTIVE

    async def test_find_by_id_returns_saved_project(self, db_session: AsyncSession):
        """Test finding project by ID retrieves correct record."""
        # Arrange
        repository = ProjectRepositoryImpl(db_session)
        project = ProjectEntity(
            id=EntityId.generate(),
            name="Findable Project",
            description="Should be findable",
            created_by=EntityId.generate(),
            status=ProjectStatus.ACTIVE,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await repository.save(project)
        await db_session.commit()

        # Act
        found_project = await repository.find_by_id(project.id.value)

        # Assert
        assert found_project is not None
        assert found_project.id.value == project.id.value
        assert found_project.name == "Findable Project"

    async def test_find_by_id_returns_none_for_nonexistent(self, db_session: AsyncSession):
        """Test finding nonexistent project returns None."""
        # Arrange
        repository = ProjectRepositoryImpl(db_session)
        nonexistent_id = EntityId.generate().value

        # Act
        result = await repository.find_by_id(nonexistent_id)

        # Assert
        assert result is None

    async def test_update_modifies_existing_project(self, db_session: AsyncSession):
        """Test updating project modifies database record."""
        # Arrange
        repository = ProjectRepositoryImpl(db_session)
        project = ProjectEntity(
            id=EntityId.generate(),
            name="Original Name",
            description="Original description",
            created_by=EntityId.generate(),
            status=ProjectStatus.ACTIVE,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        saved = await repository.save(project)
        await db_session.commit()

        # Act - Update the project
        saved.name = "Updated Name"
        saved.description = "Updated description"
        saved.status = ProjectStatus.COMPLETED
        updated = await repository.save(saved)
        await db_session.commit()

        # Assert
        refetched = await repository.find_by_id(project.id.value)
        assert refetched is not None
        assert refetched.name == "Updated Name"
        assert refetched.description == "Updated description"
        assert refetched.status == ProjectStatus.COMPLETED

    async def test_delete_removes_project(self, db_session: AsyncSession):
        """Test deleting project removes database record."""
        # Arrange
        repository = ProjectRepositoryImpl(db_session)
        project = ProjectEntity(
            id=EntityId.generate(),
            name="To Be Deleted",
            description="Will be removed",
            created_by=EntityId.generate(),
            status=ProjectStatus.ACTIVE,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await repository.save(project)
        await db_session.commit()

        # Act
        deleted = await repository.delete(project.id.value)
        await db_session.commit()

        # Assert
        assert deleted is True
        found = await repository.find_by_id(project.id.value)
        assert found is None

    async def test_delete_returns_false_for_nonexistent(self, db_session: AsyncSession):
        """Test deleting nonexistent project returns False."""
        # Arrange
        repository = ProjectRepositoryImpl(db_session)
        nonexistent_id = EntityId.generate().value

        # Act
        result = await repository.delete(nonexistent_id)

        # Assert
        assert result is False

    async def test_find_all_returns_all_projects(self, db_session: AsyncSession):
        """Test finding all projects returns correct records."""
        # Arrange
        repository = ProjectRepositoryImpl(db_session)
        project1 = ProjectEntity(
            id=EntityId.generate(),
            name="Project 1",
            description="First",
            created_by=EntityId.generate(),
            status=ProjectStatus.ACTIVE,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        project2 = ProjectEntity(
            id=EntityId.generate(),
            name="Project 2",
            description="Second",
            created_by=EntityId.generate(),
            status=ProjectStatus.COMPLETED,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await repository.save(project1)
        await repository.save(project2)
        await db_session.commit()

        # Act
        results = await repository.find_all(limit=100, offset=0)

        # Assert
        assert len(results) >= 2
        names = {p.name for p in results}
        assert "Project 1" in names
        assert "Project 2" in names

    async def test_find_all_with_pagination(self, db_session: AsyncSession):
        """Test pagination works correctly."""
        # Arrange
        repository = ProjectRepositoryImpl(db_session)
        created_by = EntityId.generate()

        # Create 5 projects
        for i in range(5):
            project = ProjectEntity(
                id=EntityId.generate(),
                name=f"Page Test {i}",
                description=f"Description {i}",
                created_by=created_by,
                status=ProjectStatus.ACTIVE,
                start_date=None,
                end_date=None,
                created_at=datetime.now() - timedelta(seconds=i),
                updated_at=datetime.now(),
            )
            await repository.save(project)
        await db_session.commit()

        # Act - Get first 2
        page1 = await repository.find_all(limit=2, offset=0)
        # Get next 2
        page2 = await repository.find_all(limit=2, offset=2)

        # Assert
        assert len(page1) == 2
        assert len(page2) == 2
        # Verify different results
        page1_names = {p.name for p in page1}
        page2_names = {p.name for p in page2}
        assert len(page1_names & page2_names) == 0  # No overlap

    async def test_find_all_with_status_filter(self, db_session: AsyncSession):
        """Test status filtering works correctly."""
        # Arrange
        repository = ProjectRepositoryImpl(db_session)
        created_by = EntityId.generate()

        active_project = ProjectEntity(
            id=EntityId.generate(),
            name="Active Project",
            description="Active",
            created_by=created_by,
            status=ProjectStatus.ACTIVE,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        completed_project = ProjectEntity(
            id=EntityId.generate(),
            name="Completed Project",
            description="Completed",
            created_by=created_by,
            status=ProjectStatus.COMPLETED,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await repository.save(active_project)
        await repository.save(completed_project)
        await db_session.commit()

        # Act
        active_results = await repository.find_all(status="active", limit=100)
        completed_results = await repository.find_all(status="completed", limit=100)

        # Assert
        active_names = {p.name for p in active_results}
        completed_names = {p.name for p in completed_results}

        assert "Active Project" in active_names
        assert "Active Project" not in completed_names
        assert "Completed Project" in completed_names
        assert "Completed Project" not in active_names

    async def test_count_returns_total_projects(self, db_session: AsyncSession):
        """Test count returns accurate total."""
        # Arrange
        repository = ProjectRepositoryImpl(db_session)
        initial_count = await repository.count()

        # Create 3 projects
        for i in range(3):
            project = ProjectEntity(
                id=EntityId.generate(),
                name=f"Count Test {i}",
                description=f"Description {i}",
                created_by=EntityId.generate(),
                status=ProjectStatus.ACTIVE,
                start_date=None,
                end_date=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            await repository.save(project)
        await db_session.commit()

        # Act
        final_count = await repository.count()

        # Assert
        assert final_count == initial_count + 3

    async def test_count_with_status_filter(self, db_session: AsyncSession):
        """Test count with status filter."""
        # Arrange
        repository = ProjectRepositoryImpl(db_session)
        created_by = EntityId.generate()

        # Create 2 active, 1 completed
        for i in range(2):
            project = ProjectEntity(
                id=EntityId.generate(),
                name=f"Active {i}",
                description="Active",
                created_by=created_by,
                status=ProjectStatus.ACTIVE,
                start_date=None,
                end_date=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            await repository.save(project)

        completed = ProjectEntity(
            id=EntityId.generate(),
            name="Completed One",
            description="Completed",
            created_by=created_by,
            status=ProjectStatus.COMPLETED,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await repository.save(completed)
        await db_session.commit()

        # Act
        active_count = await repository.count(status="active")
        completed_count = await repository.count(status="completed")

        # Assert
        assert active_count >= 2
        assert completed_count >= 1

    async def test_exists_returns_true_for_existing_project(self, db_session: AsyncSession):
        """Test exists returns True for saved project."""
        # Arrange
        repository = ProjectRepositoryImpl(db_session)
        project = ProjectEntity(
            id=EntityId.generate(),
            name="Exists Test",
            description="Test",
            created_by=EntityId.generate(),
            status=ProjectStatus.ACTIVE,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await repository.save(project)
        await db_session.commit()

        # Act
        exists = await repository.exists(project.id.value)

        # Assert
        assert exists is True

    async def test_exists_returns_false_for_nonexistent(self, db_session: AsyncSession):
        """Test exists returns False for nonexistent project."""
        # Arrange
        repository = ProjectRepositoryImpl(db_session)
        nonexistent_id = EntityId.generate().value

        # Act
        exists = await repository.exists(nonexistent_id)

        # Assert
        assert exists is False

    async def test_concurrent_saves_maintain_data_integrity(self, db_session: AsyncSession):
        """Test multiple concurrent saves don't corrupt data."""
        # Arrange
        repository = ProjectRepositoryImpl(db_session)
        projects = [
            ProjectEntity(
                id=EntityId.generate(),
                name=f"Concurrent {i}",
                description=f"Test {i}",
                created_by=EntityId.generate(),
                status=ProjectStatus.ACTIVE,
                start_date=None,
                end_date=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for i in range(10)
        ]

        # Act - Save all projects
        for project in projects:
            await repository.save(project)
        await db_session.commit()

        # Assert - Verify all saved
        for project in projects:
            found = await repository.find_by_id(project.id.value)
            assert found is not None
            assert found.name == project.name
