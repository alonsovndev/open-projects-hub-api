"""
Tests for GenerateStoriesFromNotesUseCase.

Tests story generation from raw notes including AI service mocking.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.app.features.refinement.application.dtos.refinement_dto import GenerateStoriesRequest
from src.app.features.refinement.application.use_cases.generate_stories_from_notes import (
    GenerateStoriesFromNotesUseCase,
)
from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.value_objects.refinement_status import RefinementStatus
from src.app.features.refinement.infrastructure.ai.ai_service import (
    AIServiceError,
    BulkGenerationResult,
    GeneratedStory,
)
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestGenerateStoriesFromNotesUseCase:
    """Test GenerateStoriesFromNotesUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_generates_stories_successfully(self):
        """Test successful story generation with AI mock."""
        mock_repo = AsyncMock()
        mock_ai_service = AsyncMock()

        project_id = EntityId.generate()
        created_by = EntityId.generate()

        ai_result = BulkGenerationResult(
            stories=[
                GeneratedStory(
                    title="Story 1",
                    description="Description 1",
                    acceptance_criteria=["Criterion 1"],
                    confidence=0.9,
                ),
                GeneratedStory(
                    title="Story 2",
                    description="Description 2",
                    acceptance_criteria=["Criterion 2"],
                    confidence=0.8,
                ),
            ],
            raw_notes="Some raw notes",
        )
        mock_ai_service.generate_stories_from_notes.return_value = ai_result

        saved_draft = StoryDraftEntity(
            id=EntityId.generate(),
            title="Story 1",
            description="Description 1",
            acceptance_criteria=["Criterion 1"],
            project_id=project_id,
            created_by=created_by,
            status=RefinementStatus.DRAFT,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        mock_repo.save.return_value = saved_draft

        use_case = GenerateStoriesFromNotesUseCase(mock_repo, mock_ai_service)

        request = GenerateStoriesRequest(
            project_id=str(project_id.value),
            raw_notes="Some raw notes that are long enough",
        )
        result = await use_case.execute(
            request=request,
            created_by=str(created_by.value),
        )

        assert result is not None
        assert len(result.stories) == 2
        assert result.stories[0].title == "Story 1"
        assert result.stories[0].confidence == 0.9
        assert result.raw_notes == "Some raw notes that are long enough"
        assert mock_ai_service.generate_stories_from_notes.call_count == 1
        assert mock_repo.save.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_ai_service_failure(self):
        """Test that AI service error propagates."""
        mock_repo = AsyncMock()
        mock_ai_service = AsyncMock()

        mock_ai_service.generate_stories_from_notes.side_effect = AIServiceError("AI service unavailable")

        use_case = GenerateStoriesFromNotesUseCase(mock_repo, mock_ai_service)

        request = GenerateStoriesRequest(
            project_id=str(uuid4()),
            raw_notes="Some raw notes that are long enough",
        )

        with pytest.raises(AIServiceError, match="AI service unavailable"):
            await use_case.execute(
                request=request,
                created_by=str(uuid4()),
            )

        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_empty_raw_notes(self):
        """Test that empty raw notes raises ValidationError at DTO level."""
        mock_ai_service = AsyncMock()

        with pytest.raises(ValidationError, match="Raw notes cannot be empty"):
            GenerateStoriesRequest(
                project_id=str(uuid4()),
                raw_notes="",
            )

        mock_ai_service.generate_stories_from_notes.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_short_raw_notes(self):
        """Test that raw notes < 20 chars raises ValidationError at DTO level."""
        mock_ai_service = AsyncMock()

        with pytest.raises(ValidationError, match="Raw notes must be at least 20 characters"):
            GenerateStoriesRequest(
                project_id=str(uuid4()),
                raw_notes="Too short",
            )

        mock_ai_service.generate_stories_from_notes.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_empty_project_id(self):
        """Test that empty project_id raises ValidationError at DTO level."""
        mock_ai_service = AsyncMock()

        with pytest.raises(ValidationError, match="Project ID is required"):
            GenerateStoriesRequest(
                project_id="",
                raw_notes="Some raw notes that are long enough",
            )

        mock_ai_service.generate_stories_from_notes.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_generates_single_story(self):
        """Test generating a single story."""
        mock_repo = AsyncMock()
        mock_ai_service = AsyncMock()

        project_id = EntityId.generate()
        created_by = EntityId.generate()

        ai_result = BulkGenerationResult(
            stories=[
                GeneratedStory(
                    title="Single Story",
                    description="Single description",
                    acceptance_criteria=["Single criterion"],
                    confidence=0.95,
                ),
            ],
            raw_notes="Notes",
        )
        mock_ai_service.generate_stories_from_notes.return_value = ai_result

        saved_draft = StoryDraftEntity(
            id=EntityId.generate(),
            title="Single Story",
            description="Single description",
            acceptance_criteria=["Single criterion"],
            project_id=project_id,
            created_by=created_by,
            status=RefinementStatus.DRAFT,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        mock_repo.save.return_value = saved_draft

        use_case = GenerateStoriesFromNotesUseCase(mock_repo, mock_ai_service)

        request = GenerateStoriesRequest(
            project_id=str(project_id.value),
            raw_notes="Some raw notes that are long enough",
        )
        result = await use_case.execute(
            request=request,
            created_by=str(created_by.value),
        )

        assert len(result.stories) == 1
        assert result.stories[0].title == "Single Story"
