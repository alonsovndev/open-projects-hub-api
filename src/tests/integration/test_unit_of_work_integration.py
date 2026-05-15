"""
Integration tests for Unit of Work pattern.

Tests real database transactions across multiple repositories.
"""
import pytest
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.email import Email
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.unit_of_work_impl import SqlAlchemyUnitOfWork


@pytest.mark.e2e
@pytest.mark.asyncio
class TestUnitOfWorkIntegration:
    """Integration tests for Unit of Work with real database."""
    
    # === Atomic Multi-Repository Operations ===
    
    async def test_create_project_with_stories_atomically(self, db_session: AsyncSession, test_user):
        """Test creating project and stories in single transaction."""
        uow = SqlAlchemyUnitOfWork(db_session)
        
        # Create project and stories atomically
        async with uow:
            # Create project
            project = ProjectEntity.create(
                name="Test Project",
                description="Project with stories",
                owner_id=test_user.id,
                status=ProjectStatus.ACTIVE,
            )
            saved_project = await uow.projects.save(project)
            assert saved_project is not None
            
            # Create multiple stories for project
            story1 = StoryEntity.create(
                title="Story 1",
                project_id=saved_project.id,
                created_by=test_user.id,
                priority=StoryPriority.HIGH,
            )
            story2 = StoryEntity.create(
                title="Story 2",
                project_id=saved_project.id,
                created_by=test_user.id,
                priority=StoryPriority.MEDIUM,
            )
            
            saved_story1 = await uow.stories.save(story1)
            saved_story2 = await uow.stories.save(story2)
            
            assert saved_story1 is not None
            assert saved_story2 is not None
            
            # Commit transaction
            await uow.commit()
        
        # Verify all data persisted
        uow2 = SqlAlchemyUnitOfWork(db_session)
        async with uow2:
            # Check project exists
            found_project = await uow2.projects.find_by_id(saved_project.id.value)
            assert found_project is not None
            assert found_project.name == "Test Project"
            
            # Check stories exist
            stories = await uow2.stories.find_all(
                project_id=saved_project.id.value,
                limit=10,
                offset=0,
            )
            assert len(stories) == 2
            assert {s.title for s in stories} == {"Story 1", "Story 2"}
    
    async def test_rollback_on_error_prevents_all_changes(self, db_session: AsyncSession, test_user):
        """Test that error during transaction rolls back all changes."""
        uow = SqlAlchemyUnitOfWork(db_session)
        
        # Attempt transaction that will fail
        with pytest.raises(ValueError):
            async with uow:
                # Create project
                project = ProjectEntity.create(
                    name="Project to Rollback",
                    description="Should not persist",
                    owner_id=test_user.id,
                    status=ProjectStatus.ACTIVE,
                )
                await uow.projects.save(project)
                
                # Create story
                story = StoryEntity.create(
                    title="Story to Rollback",
                    project_id=project.id,
                    created_by=test_user.id,
                )
                await uow.stories.save(story)
                
                # Simulate error before commit
                raise ValueError("Simulated error")
        
        # Verify nothing was persisted
        uow2 = SqlAlchemyUnitOfWork(db_session)
        async with uow2:
            # Project should not exist
            projects = await uow2.projects.find_all(limit=100, offset=0)
            project_names = [p.name for p in projects]
            assert "Project to Rollback" not in project_names
            
            # Story should not exist
            stories = await uow2.stories.find_all(limit=100, offset=0)
            story_titles = [s.title for s in stories]
            assert "Story to Rollback" not in story_titles
    
    async def test_update_project_and_stories_atomically(
        self, db_session: AsyncSession, test_user, test_project
    ):
        """Test updating project and its stories in single transaction."""
        uow = SqlAlchemyUnitOfWork(db_session)
        
        # Create initial stories
        async with uow:
            story1 = StoryEntity.create(
                title="Story 1",
                project_id=test_project.id,
                created_by=test_user.id,
            )
            story2 = StoryEntity.create(
                title="Story 2",
                project_id=test_project.id,
                created_by=test_user.id,
            )
            await uow.stories.save(story1)
            await uow.stories.save(story2)
            await uow.commit()
        
        # Update project and all stories atomically
        async with uow:
            # Update project status
            project = await uow.projects.find_by_id(test_project.id.value)
            project.complete()
            await uow.projects.save(project)
            
            # Update all stories to done
            stories = await uow.stories.find_all(
                project_id=test_project.id.value,
                limit=10,
                offset=0,
            )
            for story in stories:
                story.mark_done()
                await uow.stories.save(story)
            
            await uow.commit()
        
        # Verify all updates persisted
        async with uow:
            # Check project status
            updated_project = await uow.projects.find_by_id(test_project.id.value)
            assert updated_project.status == ProjectStatus.COMPLETED
            
            # Check all stories are done
            updated_stories = await uow.stories.find_all(
                project_id=test_project.id.value,
                limit=10,
                offset=0,
            )
            assert all(s.status.value == "done" for s in updated_stories)
    
    async def test_delete_project_cascades_to_stories(
        self, db_session: AsyncSession, test_user, test_project
    ):
        """Test deleting project with manual story cleanup in transaction."""
        uow = SqlAlchemyUnitOfWork(db_session)
        
        # Create stories for project
        async with uow:
            story1 = StoryEntity.create(
                title="Story to Delete 1",
                project_id=test_project.id,
                created_by=test_user.id,
            )
            story2 = StoryEntity.create(
                title="Story to Delete 2",
                project_id=test_project.id,
                created_by=test_user.id,
            )
            saved_story1 = await uow.stories.save(story1)
            saved_story2 = await uow.stories.save(story2)
            await uow.commit()
        
        # Delete stories and project atomically
        async with uow:
            # Delete stories first
            await uow.stories.delete(saved_story1.id.value)
            await uow.stories.delete(saved_story2.id.value)
            
            # Then delete project
            await uow.projects.delete(test_project.id.value)
            
            await uow.commit()
        
        # Verify all deleted
        async with uow:
            # Project should be gone
            found_project = await uow.projects.find_by_id(test_project.id.value)
            assert found_project is None
            
            # Stories should be gone
            found_story1 = await uow.stories.find_by_id(saved_story1.id.value)
            found_story2 = await uow.stories.find_by_id(saved_story2.id.value)
            assert found_story1 is None
            assert found_story2 is None
    
    # === Cross-Feature Operations ===
    
    async def test_create_user_and_project_atomically(self, db_session: AsyncSession):
        """Test creating user and their first project atomically."""
        uow = SqlAlchemyUnitOfWork(db_session)
        
        async with uow:
            # Create new user
            user = UserEntity.create(
                name="New User",
                email=Email("newuser@example.com"),
                password_hash="$2b$12$hash",
                role=UserRole.USER,
            )
            saved_user = await uow.users.save(user)
            assert saved_user is not None
            
            # Create their first project
            project = ProjectEntity.create(
                name="User's First Project",
                description="Created with user",
                owner_id=saved_user.id,
                status=ProjectStatus.ACTIVE,
            )
            saved_project = await uow.projects.save(project)
            assert saved_project is not None
            
            await uow.commit()
        
        # Verify both persisted
        async with uow:
            found_user = await uow.users.find_by_email(Email("newuser@example.com"))
            assert found_user is not None
            
            found_project = await uow.projects.find_by_id(saved_project.id.value)
            assert found_project is not None
            assert found_project.owner_id == found_user.id
    
    # === Isolation Tests ===
    
    async def test_concurrent_uow_instances_are_isolated(
        self, db_session: AsyncSession, test_user
    ):
        """Test that multiple UoW instances don't interfere."""
        # Note: This test uses the same session, so not true concurrency
        # But demonstrates separate UoW instances
        
        uow1 = SqlAlchemyUnitOfWork(db_session)
        
        # First transaction
        async with uow1:
            project1 = ProjectEntity.create(
                name="Project 1",
                description="First transaction",
                owner_id=test_user.id,
                status=ProjectStatus.ACTIVE,
            )
            saved_project1 = await uow1.projects.save(project1)
            await uow1.commit()
        
        # Second transaction with new UoW
        uow2 = SqlAlchemyUnitOfWork(db_session)
        async with uow2:
            project2 = ProjectEntity.create(
                name="Project 2",
                description="Second transaction",
                owner_id=test_user.id,
                status=ProjectStatus.ACTIVE,
            )
            saved_project2 = await uow2.projects.save(project2)
            await uow2.commit()
        
        # Verify both projects exist
        uow3 = SqlAlchemyUnitOfWork(db_session)
        async with uow3:
            all_projects = await uow3.projects.find_all(limit=100, offset=0)
            project_names = {p.name for p in all_projects}
            assert "Project 1" in project_names
            assert "Project 2" in project_names
    
    # === Error Handling Tests ===
    
    async def test_constraint_violation_rolls_back_transaction(
        self, db_session: AsyncSession, test_user
    ):
        """Test that constraint violations roll back entire transaction."""
        uow = SqlAlchemyUnitOfWork(db_session)
        
        # Create valid project first
        async with uow:
            project = ProjectEntity.create(
                name="Valid Project",
                description="Should persist",
                owner_id=test_user.id,
                status=ProjectStatus.ACTIVE,
            )
            await uow.projects.save(project)
            await uow.commit()
        
        # Attempt transaction with invalid foreign key
        from sqlalchemy.exc import IntegrityError
        
        with pytest.raises(Exception):  # Will be wrapped in UoW exception
            async with uow:
                # Valid story
                story1 = StoryEntity.create(
                    title="Valid Story",
                    project_id=project.id,
                    created_by=test_user.id,
                )
                await uow.stories.save(story1)
                
                # Invalid story (non-existent project)
                story2 = StoryEntity.create(
                    title="Invalid Story",
                    project_id=EntityId(uuid4()),  # Does not exist
                    created_by=test_user.id,
                )
                await uow.stories.save(story2)
                
                # This commit will fail due to FK constraint
                await uow.commit()
        
        # Verify valid story was rolled back (not persisted)
        async with uow:
            stories = await uow.stories.find_all(
                project_id=project.id.value,
                limit=10,
                offset=0,
            )
            # Should be empty (rollback prevented persistence)
            assert len(stories) == 0
    
    # === Repository Sharing Tests ===
    
    async def test_repositories_share_transaction_state(
        self, db_session: AsyncSession, test_user
    ):
        """Test that all repositories see uncommitted changes within transaction."""
        uow = SqlAlchemyUnitOfWork(db_session)
        
        async with uow:
            # Create project
            project = ProjectEntity.create(
                name="Shared Transaction Project",
                description="Test",
                owner_id=test_user.id,
                status=ProjectStatus.ACTIVE,
            )
            saved_project = await uow.projects.save(project)
            
            # Create story referencing uncommitted project
            story = StoryEntity.create(
                title="Story in Transaction",
                project_id=saved_project.id,
                created_by=test_user.id,
            )
            saved_story = await uow.stories.save(story)
            
            # Both should be findable within transaction
            found_project = await uow.projects.find_by_id(saved_project.id.value)
            found_story = await uow.stories.find_by_id(saved_story.id.value)
            
            assert found_project is not None
            assert found_story is not None
            assert found_story.project_id == found_project.id
            
            await uow.commit()
