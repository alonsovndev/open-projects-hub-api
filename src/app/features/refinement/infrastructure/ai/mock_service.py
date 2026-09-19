"""Mock AI service for development/testing when no API key is configured."""

from src.app.features.refinement.infrastructure.ai.ai_service import AIService, BulkGenerationResult, GeneratedStory


class MockAIService(AIService):
    """
    Mock AI service that returns sensible refinements without calling an API.

    Used during development or when no AI provider is configured.
    """

    async def is_available(self) -> bool:
        """Mock service is always available."""
        return True

    async def generate_stories_from_notes(
        self,
        raw_notes: str,
    ) -> BulkGenerationResult:
        """Generate mock stories from raw notes."""
        # Extract potential stories from notes
        stories = [
            GeneratedStory(
                title="User Authentication",
                description="As a user, I want to securely log in to the system so that I can access my personal data.",
                acceptance_criteria=[
                    "Given I am on the login page, When I enter valid credentials, Then I am logged in successfully",
                    "Given I am on the login page, When I enter invalid credentials, Then I see an error message",
                ],
            ),
            GeneratedStory(
                title="File Upload Functionality",
                description="As a client, I want to upload files securely so that I can share assets with the team.",
                acceptance_criteria=[
                    "Given I am on the upload page, When I drag and drop a file, Then the file is uploaded",
                    "Given a file is uploaded, When the file size exceeds limit, Then I see an error message",
                ],
            ),
        ]

        return BulkGenerationResult(
            stories=stories,
            raw_notes=raw_notes,
        )
