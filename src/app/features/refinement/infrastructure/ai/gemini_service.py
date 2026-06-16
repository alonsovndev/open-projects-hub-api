"""Google Gemini service implementation for story refinement."""

import json
import re

import httpx

from src.app.features.refinement.infrastructure.ai.ai_service import (
    AIService,
    AIServiceError,
    BulkGenerationResult,
    GeneratedStory,
)
from src.app.shared.logging import IntegrationLogger, get_logger


class GeminiService(AIService):
    """
    Google Gemini-based implementation of AIService.

    Uses the Gemini REST API directly via httpx
    (no SDK dependency required).
    """

    BULK_GENERATION_PROMPT = """You are an expert Agile product owner and business analyst.
Your task is to analyze raw discovery notes and generate accurate, well-structured user stories.

Rules:
1. Identify only the most meaningful, distinct features/requirements from the notes
2. Generate 2-4 high-quality user stories (quality over quantity)
3. Each story must have:
   - Clear, concise title that captures the core need
   - Description in format: "As a [role], I want to [action] so that [benefit]"
   - 2-4 acceptance criteria in Given-When-Then format
4. Prioritize the most impactful stories; skip trivial or ambiguous items
5. Ensure each story is independent, testable, and delivers real business value

Return ONLY a valid JSON object with this exact structure:
{
  "stories": [
    {
      "title": "string",
      "description": "string",
      "acceptance_criteria": ["string", "string", ...],
    }
  ]
}"""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta/models",
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ):
        """
        Initialize Gemini service.

        Args:
            api_key: Google AI Studio API key
            model: Gemini model to use
            base_url: API base URL
            temperature: Sampling temperature (lower = more deterministic)
            max_tokens: Maximum response tokens
        """
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._log = IntegrationLogger(get_logger(__name__), service_name="gemini")

    async def is_available(self) -> bool:
        """Check if Gemini service is configured."""
        return bool(self._api_key and self._api_key.strip())

    async def generate_stories_from_notes(
        self,
        raw_notes: str,
    ) -> BulkGenerationResult:
        """
        Generate user stories from raw discovery notes.

        Args:
            raw_notes: Raw discovery notes, requirements, or meeting notes

        Returns:
            BulkGenerationResult with generated stories

        Raises:
            AIServiceError: If AI service call fails
        """
        url = f"{self._base_url}/{self._model}:generateContent?key={self._api_key}"

        user_prompt = f"Analyze these discovery notes and generate user stories:\n\n{raw_notes}"

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [
                            {
                                "role": "user",
                                "parts": [
                                    {"text": self.BULK_GENERATION_PROMPT},
                                    {"text": user_prompt},
                                ],
                            }
                        ],
                        "generationConfig": {
                            "temperature": self._temperature,
                            "maxOutputTokens": 2500,  # Focused output for 2-4 stories
                            "responseMimeType": "application/json",
                            "responseSchema": {
                                "type": "object",
                                "properties": {
                                    "stories": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "title": {"type": "string"},
                                                "description": {"type": "string"},
                                                "acceptance_criteria": {"type": "array", "items": {"type": "string"}},
                                            },
                                            "required": ["title", "description", "acceptance_criteria"],
                                        },
                                    }
                                },
                                "required": ["stories"],
                            },
                        },
                    },
                )

                if response.status_code != 200:
                    raise AIServiceError(f"Gemini API error: {response.status_code} - {response.text}")

                data = response.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"]

                self._log.debug(f"Gemini bulk generation response length: {len(content)} chars")

                return self._parse_bulk_generation(content, raw_notes)

        except AIServiceError:
            raise
        except Exception as e:
            raise AIServiceError(f"Failed to call Gemini API for bulk generation: {e!s}") from e

    def _parse_bulk_generation(self, content: str, raw_notes: str) -> BulkGenerationResult:
        """Parse the bulk generation response JSON."""
        try:
            # Clean up content
            json_str = content.strip()
            if "```" in json_str:
                match = re.search(r"```(?:json)?\s*(.*?)\s*```", json_str, re.DOTALL)
                if match:
                    json_str = match.group(1).strip()

            # Parse JSON
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                self._log.warning(f"Malformed JSON from bulk generation: {e!s}")
                json_str = re.sub(r",(\s*[}\]])", r"\1", json_str)
                data = json.loads(json_str)

            stories = []
            for story_data in data.get("stories", []):
                stories.append(
                    GeneratedStory(
                        title=story_data.get("title", "Untitled Story"),
                        description=story_data.get("description", ""),
                        acceptance_criteria=story_data.get("acceptance_criteria", []),
                    )
                )

            return BulkGenerationResult(
                stories=stories,
                raw_notes=raw_notes,
            )

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            self._log.error(f"Failed to parse bulk generation response: {e}")
            self._log.error(f"Content that failed: {content[:1000]}")
            raise AIServiceError(f"Invalid bulk generation response format: {e!s}") from e
