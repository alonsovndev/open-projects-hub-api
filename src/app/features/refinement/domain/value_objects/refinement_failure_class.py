"""Refinement failure classification."""

from enum import StrEnum


class RefinementFailureClass(StrEnum):
    """
    Why a refinement run failed, coarse enough to log and show without leaking detail.

    Used to decide whether a retry is worth offering and to group provider outages in logs.
    """

    TIMEOUT = "timeout"
    PROVIDER_ERROR = "provider_error"
    INVALID_RESPONSE = "invalid_response"

    @property
    def guidance(self) -> str:
        """Actionable, credential-free message for the Admin."""
        match self:
            case RefinementFailureClass.TIMEOUT:
                return "The AI provider took too long to respond. Your notes were kept — retry when ready."
            case RefinementFailureClass.PROVIDER_ERROR:
                return "The AI provider rejected the request. Your notes were kept — retry in a moment."
            case RefinementFailureClass.INVALID_RESPONSE:
                return "The AI provider returned an unusable response. Your notes were kept — retry to generate again."
