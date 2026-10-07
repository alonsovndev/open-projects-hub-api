"""Renders an approved backlog as a stakeholder-readable Markdown document."""

from datetime import date

from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.stories.domain.entities.story_entity import StoryEntity


EMPTY_BACKLOG_NOTICE = "_No approved stories match this scope._"


def render_backlog_markdown(project: ProjectEntity, stories: list[StoryEntity], generated_on: date) -> str:
    """
    Render a project's backlog as Markdown.

    Pure by design — it takes the already-loaded project and stories and touches no clock,
    database or filesystem, so the exact document can be asserted in a unit test.

    A scope with no stories still produces a document rather than an error: the Admin is
    warned separately, and an empty template is a usable starting point.

    Args:
        project: The project the backlog belongs to
        stories: Stories already narrowed and ordered by the caller
        generated_on: The date to stamp on the document

    Returns:
        The Markdown document as a string
    """
    lines: list[str] = [
        f"# {project.name} — Requirements Backlog",
        "",
        f"**Project code:** {project.code}",
        f"**Generated on:** {generated_on.isoformat()}",
        f"**Stories:** {len(stories)}",
    ]

    if project.description:
        lines += ["", project.description]

    lines += ["", "---"]

    if not stories:
        lines += ["", EMPTY_BACKLOG_NOTICE, ""]
        return "\n".join(lines)

    for position, story in enumerate(stories, start=1):
        lines += _render_story(position, story)

    return "\n".join(lines)


def _render_story(position: int, story: StoryEntity) -> list[str]:
    """Render one story as the standard template: heading, metadata, body, criteria."""
    lines = [
        "",
        f"## {position}. {story.title}",
        "",
        f"**Status:** {story.status.value} · **Priority:** {story.priority.value}",
    ]

    if story.points is not None:
        lines.append(f"**Story points:** {story.points}")

    if story.description:
        lines += ["", story.description]

    if story.acceptance_criteria:
        lines += ["", "### Acceptance Criteria", ""]
        lines += [f"- {criterion}" for criterion in story.acceptance_criteria]

    lines += ["", "---"]
    return lines
