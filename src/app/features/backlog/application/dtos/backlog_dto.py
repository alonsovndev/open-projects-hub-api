"""Backlog view and Markdown export DTOs."""

from dataclasses import dataclass
from datetime import date

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.alias_generators import to_camel

from src.app.features.stories.domain.value_objects.story_status import StoryStatus


class BacklogStoryResponse(BaseModel):
    """A single approved story as the backlog view presents it."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str
    title: str
    description: str | None
    acceptance_criteria: list[str]
    status: str
    priority: str
    points: int | None
    created_at: str
    updated_at: str


class MarkdownExportRequest(BaseModel):
    """
    Scope for a Markdown export.

    Every field is optional; an empty body exports the project's whole backlog. `status`
    filters on the story lifecycle (todo/in_progress/blocked/done) rather than on approval
    state — a row in the backlog is approved by definition, since unapproved work is still
    a draft and lives outside this table.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    status: StoryStatus | None = None
    date_from: date | None = None
    date_to: date | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> "MarkdownExportRequest":
        """Reject an inverted range rather than silently exporting nothing."""
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("dateFrom cannot be later than dateTo")
        return self


@dataclass(frozen=True)
class MarkdownExport:
    """
    A rendered export, before it becomes an HTTP response.

    Keeps the use case free of framework types: the route decides the headers.

    Attributes:
        filename: Suggested download filename
        content: The Markdown document
        story_count: How many stories the document actually contains
        matched_count: How many stories the scope matched, before the export cap
    """

    filename: str
    content: str
    story_count: int
    matched_count: int

    @property
    def is_truncated(self) -> bool:
        """Whether the export cap held stories back from the document."""
        return self.matched_count > self.story_count
