"""AI service interface for story refinement."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class GeneratedStory:
    """A single generated story from raw discovery notes."""

    title: str
    description: str
    acceptance_criteria: list[str]


@dataclass
class BulkGenerationResult:
    """Result from bulk story generation."""

    stories: list[GeneratedStory]
    raw_notes: str


class AIService(ABC):
    """Abstract interface for AI-powered story refinement."""

    @abstractmethod
    async def generate_stories_from_notes(
        self,
        raw_notes: str,
    ) -> BulkGenerationResult:
        """
        Generate multiple user stories from raw discovery notes.

        Args:
            raw_notes: Raw discovery notes, requirements, or meeting notes

        Returns:
            BulkGenerationResult with generated stories

        Raises:
            AIServiceError: If AI service call fails
        """

    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if the AI service is available and configured.

        Returns:
            True if service is ready to use
        """


class AIServiceError(Exception):
    """Raised when AI service encounters an error."""
