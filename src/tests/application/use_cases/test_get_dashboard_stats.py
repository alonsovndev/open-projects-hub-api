"""
Tests for GetDashboardStatsUseCase.

Tests dashboard statistics retrieval including aggregated counts.
"""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.app.features.dashboard.application.dtos.dashboard_dto import DashboardStatsResponse
from src.app.features.dashboard.application.use_cases.get_dashboard_stats import GetDashboardStatsUseCase
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.value_objects.project_priority import ProjectPriority
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestGetDashboardStatsUseCase:
    """Test GetDashboardStatsUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_returns_dashboard_stats(self):
        """Test successful dashboard stats retrieval."""
        mock_dashboard_repo = AsyncMock()
        mock_project_repo = AsyncMock()
        mock_story_repo = AsyncMock()

        user_id = uuid4()

        mock_dashboard_repo.get_aggregated_stats.return_value = {
            "total_projects": 10,
            "active_projects": 7,
            "total_stories": 50,
            "assigned_stories": 12,
            "completed_stories": 15,
        }

        project1 = ProjectEntity(
            id=EntityId.generate(),
            name="Project 1",
            code="PRJ1",
            description=None,
            created_by=EntityId.generate(),
            client_id=EntityId.generate(),
            status=ProjectStatus.ACTIVE,
            priority=ProjectPriority.MEDIUM,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_project_repo.find_all.return_value = [(project1, "Client 1")]

        story1 = StoryEntity(
            id=EntityId.generate(),
            title="Story 1",
            description=None,
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.HIGH,
            points=5,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_story_repo.find_all.return_value = [story1]

        use_case = GetDashboardStatsUseCase(
            mock_dashboard_repo,
            mock_project_repo,
            mock_story_repo,
        )

        result = await use_case.execute(str(user_id))

        assert isinstance(result, DashboardStatsResponse)
        assert result.total_projects == 10
        assert result.active_projects == 7
        assert result.total_stories == 50
        assert result.assigned_stories == 12
        assert result.completed_stories == 15
        assert len(result.recent_projects) == 1
        assert len(result.recent_stories) == 1

        mock_dashboard_repo.get_aggregated_stats.assert_called_once_with(user_id)
        mock_project_repo.find_all.assert_called_once_with(limit=5)
        mock_story_repo.find_all.assert_called_once_with(limit=5)

    @pytest.mark.asyncio
    async def test_execute_with_multiple_recent_items(self):
        """Test dashboard stats with multiple recent projects and stories."""
        mock_dashboard_repo = AsyncMock()
        mock_project_repo = AsyncMock()
        mock_story_repo = AsyncMock()

        user_id = uuid4()

        mock_dashboard_repo.get_aggregated_stats.return_value = {
            "total_projects": 5,
            "active_projects": 3,
            "total_stories": 20,
            "assigned_stories": 8,
            "completed_stories": 5,
        }

        recent_projects = [
            (
                ProjectEntity(
                    id=EntityId.generate(),
                    name=f"Project {i}",
                    code=f"PRJ{i}",
                    description=None,
                    created_by=EntityId.generate(),
                    client_id=EntityId.generate(),
                    status=ProjectStatus.ACTIVE,
                    priority=ProjectPriority.MEDIUM,
                    start_date=None,
                    end_date=None,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                ),
                f"Client {i}",
            )
            for i in range(5)
        ]
        mock_project_repo.find_all.return_value = recent_projects

        recent_stories = [
            StoryEntity(
                id=EntityId.generate(),
                title=f"Story {i}",
                description=None,
                project_id=EntityId.generate(),
                created_by=EntityId.generate(),
                assigned_to=None,
                status=StoryStatus.TODO,
                priority=StoryPriority.MEDIUM,
                points=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for i in range(5)
        ]
        mock_story_repo.find_all.return_value = recent_stories

        use_case = GetDashboardStatsUseCase(
            mock_dashboard_repo,
            mock_project_repo,
            mock_story_repo,
        )

        result = await use_case.execute(str(user_id))

        assert len(result.recent_projects) == 5
        assert len(result.recent_stories) == 5
        assert result.recent_projects[0].name == "Project 0"
        assert result.recent_stories[0].title == "Story 0"

    @pytest.mark.asyncio
    async def test_execute_with_no_recent_items(self):
        """Test dashboard stats with no recent projects or stories."""
        mock_dashboard_repo = AsyncMock()
        mock_project_repo = AsyncMock()
        mock_story_repo = AsyncMock()

        user_id = uuid4()

        mock_dashboard_repo.get_aggregated_stats.return_value = {
            "total_projects": 0,
            "active_projects": 0,
            "total_stories": 0,
            "assigned_stories": 0,
            "completed_stories": 0,
        }

        mock_project_repo.find_all.return_value = []
        mock_story_repo.find_all.return_value = []

        use_case = GetDashboardStatsUseCase(
            mock_dashboard_repo,
            mock_project_repo,
            mock_story_repo,
        )

        result = await use_case.execute(str(user_id))

        assert result.total_projects == 0
        assert result.active_projects == 0
        assert result.total_stories == 0
        assert result.assigned_stories == 0
        assert result.completed_stories == 0
        assert len(result.recent_projects) == 0
        assert len(result.recent_stories) == 0

    @pytest.mark.asyncio
    async def test_execute_maps_project_summaries_correctly(self):
        """Test that project summaries are correctly mapped."""
        mock_dashboard_repo = AsyncMock()
        mock_project_repo = AsyncMock()
        mock_story_repo = AsyncMock()

        user_id = uuid4()
        project_id = EntityId.generate()
        created_at = datetime(2026, 5, 10, 12, 0, 0)

        mock_dashboard_repo.get_aggregated_stats.return_value = {
            "total_projects": 1,
            "active_projects": 1,
            "total_stories": 0,
            "assigned_stories": 0,
            "completed_stories": 0,
        }

        project = ProjectEntity(
            id=project_id,
            name="Test Project",
            code="TEST",
            description="Description",
            created_by=EntityId.generate(),
            client_id=EntityId.generate(),
            status=ProjectStatus.COMPLETED,
            priority=ProjectPriority.MEDIUM,
            start_date=None,
            end_date=None,
            created_at=created_at,
            updated_at=created_at,
        )
        mock_project_repo.find_all.return_value = [(project, "Client")]
        mock_story_repo.find_all.return_value = []

        use_case = GetDashboardStatsUseCase(
            mock_dashboard_repo,
            mock_project_repo,
            mock_story_repo,
        )

        result = await use_case.execute(str(user_id))

        project_summary = result.recent_projects[0]
        assert project_summary.id == str(project_id.value)
        assert project_summary.name == "Test Project"
        assert project_summary.status == "completed"
        assert project_summary.created_at == created_at.isoformat()

    @pytest.mark.asyncio
    async def test_execute_maps_story_summaries_correctly(self):
        """Test that story summaries are correctly mapped."""
        mock_dashboard_repo = AsyncMock()
        mock_project_repo = AsyncMock()
        mock_story_repo = AsyncMock()

        user_id = uuid4()
        story_id = EntityId.generate()
        created_at = datetime(2026, 5, 10, 14, 30, 0)

        mock_dashboard_repo.get_aggregated_stats.return_value = {
            "total_projects": 0,
            "active_projects": 0,
            "total_stories": 1,
            "assigned_stories": 1,
            "completed_stories": 0,
        }

        mock_project_repo.find_all.return_value = []

        story = StoryEntity(
            id=story_id,
            title="Test Story",
            description="Description",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
            assigned_to=EntityId.generate(),
            status=StoryStatus.IN_PROGRESS,
            priority=StoryPriority.HIGH,
            points=8,
            created_at=created_at,
            updated_at=created_at,
        )
        mock_story_repo.find_all.return_value = [story]

        use_case = GetDashboardStatsUseCase(
            mock_dashboard_repo,
            mock_project_repo,
            mock_story_repo,
        )

        result = await use_case.execute(str(user_id))

        story_summary = result.recent_stories[0]
        assert story_summary.id == str(story_id.value)
        assert story_summary.title == "Test Story"
        assert story_summary.status == "in_progress"
        assert story_summary.priority == "high"
        assert story_summary.created_at == created_at.isoformat()

    @pytest.mark.asyncio
    async def test_execute_parses_user_id_correctly(self):
        """Test that user_id string is correctly parsed to UUID."""
        mock_dashboard_repo = AsyncMock()
        mock_project_repo = AsyncMock()
        mock_story_repo = AsyncMock()

        user_id = uuid4()

        mock_dashboard_repo.get_aggregated_stats.return_value = {
            "total_projects": 0,
            "active_projects": 0,
            "total_stories": 0,
            "assigned_stories": 0,
            "completed_stories": 0,
        }
        mock_project_repo.find_all.return_value = []
        mock_story_repo.find_all.return_value = []

        use_case = GetDashboardStatsUseCase(
            mock_dashboard_repo,
            mock_project_repo,
            mock_story_repo,
        )

        await use_case.execute(str(user_id))

        called_with = mock_dashboard_repo.get_aggregated_stats.call_args[0][0]
        assert called_with == user_id
