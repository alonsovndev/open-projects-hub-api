"""Unit tests for ProjectRepositoryImpl."""
from datetime import date, datetime
from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest

from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.features.projects.infrastructure.models.project_model import ProjectModel
from src.app.features.projects.infrastructure.repositories.project_repository_impl import ProjectRepositoryImpl
from src.app.shared.domain.value_objects.entity_id import EntityId


@pytest.fixture
def mock_session():
    """Create mock async session."""
    return AsyncMock()


@pytest.fixture
def repository(mock_session):
    """Create repository with mock session."""
    return ProjectRepositoryImpl(mock_session)


@pytest.fixture
def sample_project_entity():
    """Create sample project entity."""
    return ProjectEntity.create(
        name="Test Project",
        created_by=EntityId.generate(),
        description="Test description",
        start_date=date(2026, 5, 1),
        end_date=date(2026, 12, 31),
    )


@pytest.fixture
def sample_project_model():
    """Create sample project model."""
    project_id = EntityId.generate()
    created_by = EntityId.generate()
    now = datetime.now()
    
    return ProjectModel(
        id=project_id.value,
        name="Test Project",
        description="Test description",
        created_by=created_by.value,
        status=ProjectStatus.ACTIVE.value,
        start_date=date(2026, 5, 1),
        end_date=date(2026, 12, 31),
        created_at=now,
        updated_at=now,
    )


class TestFindById:
    """Test find_by_id method."""
    
    @pytest.mark.asyncio
    async def test_find_by_id_returns_entity_when_found(self, repository, mock_session, sample_project_model):
        """Test finding project by ID returns entity when found."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_project_model
        mock_session.execute.return_value = mock_result
        
        # Act
        entity = await repository.find_by_id(sample_project_model.id)
        
        # Assert
        assert entity is not None
        assert entity.name == "Test Project"
        assert entity.description == "Test description"
        assert entity.status == ProjectStatus.ACTIVE
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_by_id_returns_none_when_not_found(self, repository, mock_session):
        """Test finding project by ID returns None when not found."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        # Act
        entity = await repository.find_by_id(EntityId.generate().value)
        
        # Assert
        assert entity is None
    
    @pytest.mark.asyncio
    async def test_find_by_id_returns_none_on_exception(self, repository, mock_session):
        """Test finding project by ID returns None when exception occurs."""
        # Arrange
        mock_session.execute.side_effect = Exception("Database error")
        
        # Act
        entity = await repository.find_by_id(EntityId.generate().value)
        
        # Assert
        assert entity is None


class TestFindAll:
    """Test find_all method."""
    
    @pytest.mark.asyncio
    async def test_find_all_returns_list_of_entities(self, repository, mock_session, sample_project_model):
        """Test finding all projects returns list of entities."""
        # Arrange
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_project_model]
        mock_session.execute.return_value = mock_result
        
        # Act
        entities = await repository.find_all()
        
        # Assert
        assert len(entities) == 1
        assert entities[0].name == "Test Project"
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_all_with_status_filter(self, repository, mock_session, sample_project_model):
        """Test finding all projects with status filter."""
        # Arrange
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_project_model]
        mock_session.execute.return_value = mock_result
        
        # Act
        entities = await repository.find_all(status="active")
        
        # Assert
        assert len(entities) == 1
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_all_with_pagination(self, repository, mock_session, sample_project_model):
        """Test finding all projects with pagination."""
        # Arrange
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_project_model]
        mock_session.execute.return_value = mock_result
        
        # Act
        entities = await repository.find_all(limit=10, offset=5)
        
        # Assert
        assert len(entities) == 1
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_all_returns_empty_list_on_exception(self, repository, mock_session):
        """Test finding all projects returns empty list on exception."""
        # Arrange
        mock_session.execute.side_effect = Exception("Database error")
        
        # Act
        entities = await repository.find_all()
        
        # Assert
        assert entities == []


class TestSave:
    """Test save method."""
    
    @pytest.mark.asyncio
    async def test_save_creates_new_project(self, repository, mock_session, sample_project_entity):
        """Test saving new project creates record."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None  # Project doesn't exist
        mock_session.execute.return_value = mock_result
        
        # Act
        saved_entity = await repository.save(sample_project_entity)
        
        # Assert
        assert saved_entity is not None
        assert saved_entity.name == "Test Project"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_updates_existing_project(self, repository, mock_session, sample_project_entity, sample_project_model):
        """Test saving existing project updates record."""
        # Arrange
        # Make entity ID match model ID
        sample_project_entity._id = EntityId.from_string(str(sample_project_model.id))
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_project_model
        mock_session.execute.return_value = mock_result
        
        # Act
        saved_entity = await repository.save(sample_project_entity)
        
        # Assert
        assert saved_entity is not None
        mock_session.add.assert_not_called()  # Should not add, only update
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_returns_none_on_exception(self, repository, mock_session, sample_project_entity):
        """Test saving project returns None on exception."""
        # Arrange
        mock_session.execute.side_effect = Exception("Database error")
        
        # Act
        saved_entity = await repository.save(sample_project_entity)
        
        # Assert
        assert saved_entity is None
        mock_session.rollback.assert_called_once()


class TestDelete:
    """Test delete method."""
    
    @pytest.mark.asyncio
    async def test_delete_returns_true_when_found(self, repository, mock_session, sample_project_model):
        """Test deleting project returns True when found."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_project_model
        mock_session.execute.return_value = mock_result
        
        # Act
        deleted = await repository.delete(sample_project_model.id)
        
        # Assert
        assert deleted is True
        mock_session.delete.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_returns_false_when_not_found(self, repository, mock_session):
        """Test deleting project returns False when not found."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        # Act
        deleted = await repository.delete(EntityId.generate().value)
        
        # Assert
        assert deleted is False
        mock_session.delete.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete_returns_false_on_exception(self, repository, mock_session):
        """Test deleting project returns False on exception."""
        # Arrange
        mock_session.execute.side_effect = Exception("Database error")
        
        # Act
        deleted = await repository.delete(EntityId.generate().value)
        
        # Assert
        assert deleted is False
        mock_session.rollback.assert_called_once()


class TestCount:
    """Test count method."""
    
    @pytest.mark.asyncio
    async def test_count_returns_total(self, repository, mock_session):
        """Test counting projects returns total."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one.return_value = 5
        mock_session.execute.return_value = mock_result
        
        # Act
        count = await repository.count()
        
        # Assert
        assert count == 5
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_count_with_status_filter(self, repository, mock_session):
        """Test counting projects with status filter."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one.return_value = 3
        mock_session.execute.return_value = mock_result
        
        # Act
        count = await repository.count(status="active")
        
        # Assert
        assert count == 3
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_count_returns_zero_on_exception(self, repository, mock_session):
        """Test counting projects returns 0 on exception."""
        # Arrange
        mock_session.execute.side_effect = Exception("Database error")
        
        # Act
        count = await repository.count()
        
        # Assert
        assert count == 0
