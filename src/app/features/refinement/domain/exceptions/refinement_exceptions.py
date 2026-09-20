"""Refinement domain exceptions."""

from src.app.features.refinement.domain.value_objects.refinement_failure_class import RefinementFailureClass


class StoryDraftNotFoundError(Exception):
    """Raised when a story draft is not found."""

    def __init__(self, draft_id: str):
        self.draft_id = draft_id
        super().__init__(f"Story draft not found: {draft_id}")


class RefinementFailedError(Exception):
    """
    Raised when a refinement run fails before any draft is persisted.

    Carries the Admin's raw notes so the API can hand them back verbatim: a provider
    outage must never cost the Admin their input (FR-002-04).
    """

    def __init__(
        self,
        failure_class: RefinementFailureClass,
        raw_notes: str,
        provider: str,
    ):
        self.failure_class = failure_class
        self.raw_notes = raw_notes
        self.provider = provider
        super().__init__(failure_class.guidance)
