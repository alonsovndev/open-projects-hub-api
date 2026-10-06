"""Tests for the project access code the client stakeholder types."""

import pytest

from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.value_objects.access_code import (
    generate_access_code,
    is_valid_access_code,
    normalize_access_code,
)
from src.app.shared.domain.value_objects.entity_id import EntityId


def build_project() -> ProjectEntity:
    return ProjectEntity.create(
        workspace_id=EntityId.generate(),
        name="Acme Portal",
        code="ACME",
        created_by=EntityId.generate(),
        client_id=EntityId.generate(),
    )


class TestGenerateAccessCode:
    def test_generated_codes_have_the_valid_shape(self):
        assert is_valid_access_code(generate_access_code())

    def test_generated_codes_avoid_look_alike_characters(self):
        suffix = "".join(generate_access_code()[4:] for _ in range(200))

        assert not set("O0I1") & set(suffix)

    def test_generated_codes_do_not_repeat(self):
        assert len({generate_access_code() for _ in range(500)}) == 500


class TestNormalizeAccessCode:
    def test_uppercases_and_trims_what_a_person_typed(self):
        assert normalize_access_code("  prj-7k3m9xq2 ") == "PRJ-7K3M9XQ2"


class TestIsValidAccessCode:
    @pytest.mark.parametrize(
        "code",
        ["", "PRJ-123456", "WEB", "PRJ-7K3M9XQ", "PRJ-7K3M9XQ22", "PRJ-7K3M9XO2", "prj-7k3m9xq2", "PRJ-7K3M 9XQ"],
    )
    def test_rejects_anything_the_generator_could_not_have_produced(self, code):
        assert not is_valid_access_code(code)


class TestProjectEntityAccessCode:
    def test_a_new_project_gets_an_access_code(self):
        assert is_valid_access_code(build_project().access_code)

    def test_two_projects_get_different_codes(self):
        assert build_project().access_code != build_project().access_code

    def test_regenerating_replaces_the_code(self):
        project = build_project()
        original_code = project.access_code

        project.regenerate_access_code()

        assert project.access_code != original_code
        assert is_valid_access_code(project.access_code)

    def test_an_existing_code_is_kept_when_loading_a_project(self):
        project = build_project()

        reloaded = ProjectEntity(
            id=project.id,
            name=project.name,
            code=project.code,
            description=None,
            created_by=project.created_by,
            client_id=project.client_id,
            status=project.status,
            priority=project.priority,
            start_date=None,
            end_date=None,
            created_at=project.created_at,
            updated_at=project.updated_at,
            access_code=project.access_code,
        )

        assert reloaded.access_code == project.access_code
