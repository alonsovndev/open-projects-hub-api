"""Mock AI service for development/testing when no API key is configured."""
from typing import List, Optional

from src.app.features.refinement.infrastructure.ai.ai_service import (
    AIService,
    BulkGenerationResult,
    GeneratedStory,
    RefinementResult,
    RefinementSuggestion,
)


class MockAIService(AIService):
    """
    Mock AI service that returns sensible refinements without calling an API.
    
    Used during development or when no AI provider is configured.
    """
    
    async def refine_story(
        self,
        title: str,
        description: Optional[str] = None,
        acceptance_criteria: Optional[List[str]] = None,
    ) -> RefinementResult:
        """Return mock refinement results."""
        # Generate a refined title
        refined_title = title
        if "login" in title.lower() or "password" in title.lower():
            refined_title = f"User Authentication - {title}"
        elif "report" in title.lower():
            refined_title = f"Reporting - {title}"
        elif "search" in title.lower():
            refined_title = f"Search & Discovery - {title}"
        
        # Generate a refined description
        refined_description = description
        if not description:
            refined_description = (
                f"As a registered user, I want to {title.lower()} "
                f"so that I can accomplish my goals efficiently."
            )
        
        # Generate refined criteria
        refined_criteria = acceptance_criteria or []
        if not refined_criteria:
            refined_criteria = [
                f"Given I am on the relevant page\nWhen I perform the action\nThen the expected outcome occurs",
                f"Given the system is in a valid state\nWhen I submit the request\nThen I receive a confirmation",
            ]
        
        suggestions = [
            RefinementSuggestion(
                suggestion_type="title",
                content=refined_title,
                reasoning="More descriptive and follows standard naming conventions",
                confidence=0.92,
            ),
            RefinementSuggestion(
                suggestion_type="description",
                content=refined_description,
                reasoning="Follows user story format with clear role, action, and benefit",
                confidence=0.88,
            ),
            RefinementSuggestion(
                suggestion_type="criteria",
                content="\n".join(refined_criteria),
                reasoning="Uses Given-When-Then format for clarity",
                confidence=0.90,
            ),
        ]
        
        return RefinementResult(
            refined_title=refined_title,
            refined_description=refined_description,
            refined_criteria=refined_criteria,
            suggestions=suggestions,
        )
    
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
                confidence=0.92,
            ),
            GeneratedStory(
                title="File Upload Functionality",
                description="As a client, I want to upload files securely so that I can share assets with the team.",
                acceptance_criteria=[
                    "Given I am on the upload page, When I drag and drop a file, Then the file is uploaded",
                    "Given a file is uploaded, When the file size exceeds limit, Then I see an error message",
                ],
                confidence=0.88,
            ),
            GeneratedStory(
                title="Team Messaging",
                description="As a client, I want to message the team directly so that I can communicate efficiently.",
                acceptance_criteria=[
                    "Given I am logged in, When I open the messaging interface, Then I can send a message",
                    "Given I send a message, When it is delivered, Then I receive a confirmation",
                ],
                confidence=0.85,
            ),
        ]
        
        return BulkGenerationResult(
            stories=stories,
            raw_notes=raw_notes,
        )
