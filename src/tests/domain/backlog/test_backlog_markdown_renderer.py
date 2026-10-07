"""Unit tests for the backlog Markdown renderer."""

from datetime import date

from src.app.features.backlog.domain.services.backlog_markdown_renderer import (
    EMPTY_BACKLOG_NOTICE,
    render_backlog_markdown,
)
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.shared.domain.value_objects.entity_id import EntityId


GENERATED_ON = date(2026, 9, 20)


def build_project(description: str | None = None) -> ProjectEntity:
    """Build a project to render a backlog for."""
    return ProjectEntity.create(
        workspace_id=EntityId.generate(),
        name="Acme Portal",
        code="ACME",
        created_by=EntityId.generate(),
        client_id=EntityId.generate(),
        description=description,
    )


def build_story(
    title: str = "Story title",
    description: str | None = "Story description",
    acceptance_criteria: list[str] | None = None,
    priority: StoryPriority | None = None,
    points: int | None = None,
) -> StoryEntity:
    """Build a story to render."""
    return StoryEntity.create(
        title=title,
        project_id=EntityId.generate(),
        created_by=EntityId.generate(),
        description=description,
        acceptance_criteria=acceptance_criteria,
        priority=priority,
        points=points,
    )


class TestBacklogHeader:
    """Test the document header."""

    def test_header_names_the_project_and_date(self):
        """Test that the header carries project name, code, date and count."""
        markdown = render_backlog_markdown(build_project(), [build_story()], GENERATED_ON)

        assert markdown.startswith("# Acme Portal — Requirements Backlog")
        assert "**Project code:** ACME" in markdown
        assert "**Generated on:** 2026-09-20" in markdown
        assert "**Stories:** 1" in markdown

    def test_project_description_is_included_when_present(self):
        """Test that a project description appears under the header."""
        markdown = render_backlog_markdown(build_project(description="Client portal rebuild"), [], GENERATED_ON)

        assert "Client portal rebuild" in markdown

    def test_project_without_description_renders_cleanly(self):
        """Test that a missing description leaves no placeholder behind."""
        markdown = render_backlog_markdown(build_project(description=None), [], GENERATED_ON)

        assert "None" not in markdown


class TestBacklogStories:
    """Test how individual stories render."""

    def test_stories_are_numbered_in_the_order_given(self):
        """The renderer does not reorder — the caller owns backlog order."""
        stories = [build_story(title="First"), build_story(title="Second"), build_story(title="Third")]

        markdown = render_backlog_markdown(build_project(), stories, GENERATED_ON)

        assert markdown.index("## 1. First") < markdown.index("## 2. Second") < markdown.index("## 3. Third")

    def test_story_shows_status_and_priority(self):
        """Test that the metadata line carries status and priority."""
        markdown = render_backlog_markdown(build_project(), [build_story(priority=StoryPriority.HIGH)], GENERATED_ON)

        assert "**Status:** todo · **Priority:** high" in markdown

    def test_points_appear_only_when_estimated(self):
        """Test that an unestimated story shows no points line."""
        with_points = render_backlog_markdown(build_project(), [build_story(points=5)], GENERATED_ON)
        without_points = render_backlog_markdown(build_project(), [build_story(points=None)], GENERATED_ON)

        assert "**Story points:** 5" in with_points
        assert "Story points" not in without_points

    def test_acceptance_criteria_render_as_a_bullet_list(self):
        """Test that criteria are listed under their own heading."""
        story = build_story(acceptance_criteria=["User can log in", "User sees the dashboard"])

        markdown = render_backlog_markdown(build_project(), [story], GENERATED_ON)

        assert "### Acceptance Criteria" in markdown
        assert "- User can log in" in markdown
        assert "- User sees the dashboard" in markdown

    def test_story_without_criteria_omits_the_heading(self):
        """Test that a story with no criteria renders no empty section."""
        markdown = render_backlog_markdown(build_project(), [build_story(acceptance_criteria=[])], GENERATED_ON)

        assert "Acceptance Criteria" not in markdown

    def test_story_without_description_omits_the_body(self):
        """Test that a description-less story does not print None."""
        markdown = render_backlog_markdown(build_project(), [build_story(description=None)], GENERATED_ON)

        assert "None" not in markdown


class TestEmptyBacklog:
    """Test the empty-scope template."""

    def test_empty_backlog_still_produces_a_document(self):
        """An empty scope is warned about, not refused — the header must survive."""
        markdown = render_backlog_markdown(build_project(), [], GENERATED_ON)

        assert "# Acme Portal — Requirements Backlog" in markdown
        assert "**Stories:** 0" in markdown
        assert EMPTY_BACKLOG_NOTICE in markdown
