"""
Integration tests for StoryRepositoryImpl.

Tests story repository implementations including foreign key constraints
with projects and users, and complex filtering queries.

Run with: pytest -m e2e
"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.infrastructure.repositories.story_repository_impl import StoryRepositoryImpl
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.features.projects.infrastructure.repositories.project_repository_impl import ProjectRepositoryImpl
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.email import Email
from src.app.features.user.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from src.app.shared.domain.value_objects.entity_id import EntityId


@pytest.mark.e2e
@pytest.mark.asyncio
class TestStoryRepositoryIntegration:
    """Integration tests for StoryRepository against real database."""
    
    @pytest.fixture
    async def test_project(self, db_session: AsyncSession) -> ProjectEntity:
        """Create a test project for foreign key relationships."""
        repository = ProjectRepositoryImpl(db_session)
        project = ProjectEntity(
            id=EntityId.generate(),
            name="Test Project",
            description="For story tests",
            created_by=EntityId.generate(),
            status=ProjectStatus.ACTIVE,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await repository.save(project)
        await db_session.commit()
        return project
    
    @pytest.fixture
    async def test_user(self, db_session: AsyncSession) -> UserEntity:
        """Create a test user for foreign key relationships."""
        repository = UserRepositoryImpl(db_session)
        user = UserEntity(
            id=EntityId.generate(),
            display_name="Test User",
            email=Email(f"test{EntityId.generate().value}@test.com"),
            password_hash="hash",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await repository.save(user)
        await db_session.commit()
        return user
    
    async def test_save_creates_new_story(
        self,
        db_session: AsyncSession,
        test_project: ProjectEntity,
        test_user: UserEntity
    ):
        """Test saving a new story creates database record."""
        # Arrange
        repository = StoryRepositoryImpl(db_session)
        story = StoryEntity(
            id=EntityId.generate(),
            title="Integration Test Story",
            description="Test story description",
            project_id=test_project.id,
            created_by=test_user.id,
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.MEDIUM,
            points=5,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        # Act
        saved_story = await repository.save(story)
        await db_session.commit()
        
        # Assert
        assert saved_story is not None
        assert saved_story.id.value == story.id.value
        assert saved_story.title == "Integration Test Story"
        assert saved_story.project_id.value == test_project.id.value
    
    async def test_foreign_key_constraint_invalid_project(
        self,
        db_session: AsyncSession,
        test_user: UserEntity
    ):
        """Test database enforces foreign key constraint for project_id."""
        # Arrange
        repository = StoryRepositoryImpl(db_session)
        nonexistent_project_id = EntityId.generate()
        
        story = StoryEntity(
            id=EntityId.generate(),
            title="Invalid Project Story",
            description="Should fail",
            project_id=nonexistent_project_id,
            created_by=test_user.id,
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.LOW,
            points=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        # Act & Assert
        with pytest.raises((IntegrityError, Exception)):
            await repository.save(story)
            await db_session.commit()
    
    async def test_find_by_project_id_returns_correct_stories(
        self,
        db_session: AsyncSession,
        test_project: ProjectEntity,
        test_user: UserEntity
    ):
        """Test finding stories by project ID."""
        # Arrange
        repository = StoryRepositoryImpl(db_session)
        
        # Create stories for the project
        for i in range(3):
            story = StoryEntity(
                id=EntityId.generate(),
                title=f"Project Story {i}",
                description=f"Story {i}",
                project_id=test_project.id,
                created_by=test_user.id,
                assigned_to=None,
                status=StoryStatus.TODO,
                priority=StoryPriority.MEDIUM,
                points=i + 1,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            await repository.save(story)
        await db_session.commit()
        
        # Act
        stories = await repository.find_by_project_id(
            project_id=test_project.id.value,
            limit=100,
            offset=0
        )
        
        # Assert
        assert len(stories) >= 3
        project_ids = {s.project_id.value for s in stories}
        assert test_project.id.value in project_ids
    
    async def test_find_all_with_status_filter(
        self,
        db_session: AsyncSession,
        test_project: ProjectEntity,
        test_user: UserEntity
    ):
        """Test filtering stories by status."""
        # Arrange
        repository = StoryRepositoryImpl(db_session)
        
        todo_story = StoryEntity(
            id=EntityId.generate(),
            title="Todo Story",
            description="Todo",
            project_id=test_project.id,
            created_by=test_user.id,
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.HIGH,
            points=3,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        in_progress_story = StoryEntity(
            id=EntityId.generate(),
            title="In Progress Story",
            description="In Progress",
            project_id=test_project.id,
            created_by=test_user.id,
            assigned_to=test_user.id,
            status=StoryStatus.IN_PROGRESS,
            priority=StoryPriority.MEDIUM,
            points=5,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        await repository.save(todo_story)
        await repository.save(in_progress_story)
        await db_session.commit()
        
        # Act
        todo_results = await repository.find_all(status="todo", limit=100)
        in_progress_results = await repository.find_all(status="in_progress", limit=100)
        
        # Assert
        todo_titles = {s.title for s in todo_results}
        in_progress_titles = {s.title for s in in_progress_results}
        
        assert "Todo Story" in todo_titles
        assert "In Progress Story" in in_progress_titles
        assert "In Progress Story" not in todo_titles
        assert "Todo Story" not in in_progress_titles
    
    async def test_find_all_with_priority_filter(
        self,
        db_session: AsyncSession,
        test_project: ProjectEntity,
        test_user: UserEntity
    ):
        """Test filtering stories by priority."""
        # Arrange
        repository = StoryRepositoryImpl(db_session)
        
        high_story = StoryEntity(
            id=EntityId.generate(),
            title="High Priority Story",
            description="High",
            project_id=test_project.id,
            created_by=test_user.id,
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.HIGH,
            points=8,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        low_story = StoryEntity(
            id=EntityId.generate(),
            title="Low Priority Story",
            description="Low",
            project_id=test_project.id,
            created_by=test_user.id,
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.LOW,
            points=2,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        await repository.save(high_story)
        await repository.save(low_story)
        await db_session.commit()
        
        # Act
        high_results = await repository.find_all(priority="high", limit=100)
        low_results = await repository.find_all(priority="low", limit=100)
        
        # Assert
        high_titles = {s.title for s in high_results}
        low_titles = {s.title for s in low_results}
        
        assert "High Priority Story" in high_titles
        assert "Low Priority Story" in low_titles
        assert "Low Priority Story" not in high_titles
        assert "High Priority Story" not in low_titles
    
    async def test_find_all_with_assigned_to_filter(
        self,
        db_session: AsyncSession,
        test_project: ProjectEntity,
        test_user: UserEntity
    ):
        """Test filtering stories by assigned user."""
        # Arrange
        repository = StoryRepositoryImpl(db_session)
        
        assigned_story = StoryEntity(
            id=EntityId.generate(),
            title="Assigned Story",
            description="Assigned",
            project_id=test_project.id,
            created_by=test_user.id,
            assigned_to=test_user.id,
            status=StoryStatus.IN_PROGRESS,
            priority=StoryPriority.MEDIUM,
            points=5,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        unassigned_story = StoryEntity(
            id=EntityId.generate(),
            title="Unassigned Story",
            description="Unassigned",
            project_id=test_project.id,
            created_by=test_user.id,
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.LOW,
            points=2,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        await repository.save(assigned_story)
        await repository.save(unassigned_story)
        await db_session.commit()
        
        # Act
        user_stories = await repository.find_all(
            assigned_to=test_user.id.value,
            limit=100
        )
        
        # Assert
        titles = {s.title for s in user_stories}
        assert "Assigned Story" in titles
        assert "Unassigned Story" not in titles
    
    async def test_count_with_multiple_filters(
        self,
        db_session: AsyncSession,
        test_project: ProjectEntity,
        test_user: UserEntity
    ):
        """Test count with multiple filter combinations."""
        # Arrange
        repository = StoryRepositoryImpl(db_session)
        
        # Create stories with different attributes
        story1 = StoryEntity(
            id=EntityId.generate(),
            title="Story 1",
            description="Test",
            project_id=test_project.id,
            created_by=test_user.id,
            assigned_to=test_user.id,
            status=StoryStatus.TODO,
            priority=StoryPriority.HIGH,
            points=5,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        story2 = StoryEntity(
            id=EntityId.generate(),
            title="Story 2",
            description="Test",
            project_id=test_project.id,
            created_by=test_user.id,
            assigned_to=test_user.id,
            status=StoryStatus.IN_PROGRESS,
            priority=StoryPriority.HIGH,
            points=3,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        await repository.save(story1)
        await repository.save(story2)
        await db_session.commit()
        
        # Act
        todo_high_count = await repository.count(status="todo", priority="high")
        in_progress_count = await repository.count(status="in_progress")
        high_priority_count = await repository.count(priority="high")
        
        # Assert
        assert todo_high_count >= 1
        assert in_progress_count >= 1
        assert high_priority_count >= 2
    
    async def test_update_story_assignment(
        self,
        db_session: AsyncSession,
        test_project: ProjectEntity,
        test_user: UserEntity
    ):
        """Test updating story assignment."""
        # Arrange
        repository = StoryRepositoryImpl(db_session)
        
        story = StoryEntity(
            id=EntityId.generate(),
            title="Assignment Test",
            description="Test",
            project_id=test_project.id,
            created_by=test_user.id,
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.MEDIUM,
            points=3,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        saved = await repository.save(story)
        await db_session.commit()
        
        # Act - Assign the story
        saved.assigned_to = test_user.id
        saved.status = StoryStatus.IN_PROGRESS
        await repository.save(saved)
        await db_session.commit()
        
        # Assert
        refetched = await repository.find_by_id(story.id.value)
        assert refetched is not None
        assert refetched.assigned_to is not None
        assert refetched.assigned_to.value == test_user.id.value
        assert refetched.status == StoryStatus.IN_PROGRESS
    
    async def test_delete_story(
        self,
        db_session: AsyncSession,
        test_project: ProjectEntity,
        test_user: UserEntity
    ):
        """Test deleting story removes record."""
        # Arrange
        repository = StoryRepositoryImpl(db_session)
        
        story = StoryEntity(
            id=EntityId.generate(),
            title="To Delete",
            description="Will be removed",
            project_id=test_project.id,
            created_by=test_user.id,
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.LOW,
            points=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        await repository.save(story)
        await db_session.commit()
        
        # Act
        deleted = await repository.delete(story.id.value)
        await db_session.commit()
        
        # Assert
        assert deleted is True
        found = await repository.find_by_id(story.id.value)
        assert found is None
    
    async def test_pagination_with_project_filter(
        self,
        db_session: AsyncSession,
        test_project: ProjectEntity,
        test_user: UserEntity
    ):
        """Test pagination works with project filter."""
        # Arrange
        repository = StoryRepositoryImpl(db_session)
        
        # Create 5 stories
        for i in range(5):
            story = StoryEntity(
                id=EntityId.generate(),
                title=f"Pagination Story {i}",
                description=f"Story {i}",
                project_id=test_project.id,
                created_by=test_user.id,
                assigned_to=None,
                status=StoryStatus.TODO,
                priority=StoryPriority.MEDIUM,
                points=i + 1,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            await repository.save(story)
        await db_session.commit()
        
        # Act
        page1 = await repository.find_by_project_id(
            project_id=test_project.id.value,
            limit=2,
            offset=0
        )
        page2 = await repository.find_by_project_id(
            project_id=test_project.id.value,
            limit=2,
            offset=2
        )
        
        # Assert
        assert len(page1) == 2
        assert len(page2) == 2
        page1_titles = {s.title for s in page1}
        page2_titles = {s.title for s in page2}
        assert len(page1_titles & page2_titles) == 0  # No overlap
