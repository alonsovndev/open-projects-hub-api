"""Client Review DTOs: what a client stakeholder sees when they open a project by access code."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from src.app.features.backlog.application.dtos.backlog_dto import BacklogStoryResponse


class ClientReviewResponse(BaseModel):
    """
    A project's approved stories, with nothing that identifies the freelancer's workspace.

    The caller is anonymous, so this deliberately omits the project id and code, the client
    record, and every user reference (creator, assignee).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    project_name: str
    phase: str
    total: int
    stories: list[BacklogStoryResponse]
