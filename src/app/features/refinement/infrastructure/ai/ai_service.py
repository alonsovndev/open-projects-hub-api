"""AI service interface for story refinement."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RefinementSuggestion:
    """A single AI suggestion for story refinement."""

    suggestion_type: str  # "title", "description", "criteria"
    content: str
    reasoning: str
    confidence: float  # 0.0 to 1.0


@dataclass
class RefinementResult:
    """Complete refinement result from AI service."""

    refined_title: str
    refined_description: str | None
    refined_criteria: list[str]
    suggestions: list[RefinementSuggestion]


@dataclass
class GeneratedStory:
    """A single generated story from raw discovery notes."""

    title: str
    description: str
    acceptance_criteria: list[str]
    confidence: float  # 0.0 to 1.0


@dataclass
class BulkGenerationResult:
    """Result from bulk story generation."""

    stories: list[GeneratedStory]
    raw_notes: str


class AIService(ABC):
    """Abstract interface for AI-powered story refinement."""

    @abstractmethod
    async def refine_story(
        self,
        title: str,
        description: str | None = None,
        acceptance_criteria: list[str] | None = None,
    ) -> RefinementResult:
        """
        Refine a user story using AI.

        Args:
            title: Raw story title
            description: Raw story description
            acceptance_criteria: Raw acceptance criteria

        Returns:
            RefinementResult with refined content and suggestions

        Raises:
            AIServiceError: If AI service call fails
        """

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
