"""Refinement domain exceptions."""

from src.app.features.refinement.domain.value_objects.refinement_failure_class import RefinementFailureClass


class RefinementFailedError(Exception):
    """
    Raised when a refinement run fails before any story is returned.

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
