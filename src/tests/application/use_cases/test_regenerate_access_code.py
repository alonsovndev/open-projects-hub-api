"""Unit tests for RegenerateAccessCodeUseCase."""

from unittest.mock import AsyncMock

import pytest

from src.app.features.projects.application.use_cases.regenerate_access_code import RegenerateAccessCodeUseCase
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.tests.support.request_context import make_request_context


def build_project() -> ProjectEntity:
    return ProjectEntity.create(
        workspace_id=EntityId.generate(),
        name="Acme Portal",
        code="ACME",
        created_by=EntityId.generate(),
        client_id=EntityId.generate(),
    )


class TestRegenerateAccessCodeUseCase:
    @pytest.mark.asyncio
    async def test_replaces_the_code_and_returns_the_new_one(self):
        project = build_project()
        original_code = project.access_code
        repository = AsyncMock()
        repository.find_by_id.return_value = (project, "Acme Ltd")
        repository.save.side_effect = lambda entity: entity
        repository.get_story_counts.return_value = (3, 1)

        result = await RegenerateAccessCodeUseCase(repository).execute(
            project_id=str(project.id.value), ctx=make_request_context()
        )

        assert result.access_code != original_code
        assert result.access_code == project.access_code
        repository.save.assert_awaited_once_with(project)

    @pytest.mark.asyncio
    async def test_a_project_outside_the_callers_workspace_is_not_found(self):
        repository = AsyncMock()
        repository.find_by_id.return_value = None

        with pytest.raises(ProjectNotFoundError):
            await RegenerateAccessCodeUseCase(repository).execute(
                project_id=str(EntityId.generate().value), ctx=make_request_context()
            )

        repository.save.assert_not_awaited()
