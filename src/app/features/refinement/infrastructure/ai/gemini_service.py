"""Google Gemini service implementation for story refinement."""

import json
import re

import httpx

from src.app.features.refinement.infrastructure.ai.ai_service import (
    AIService,
    AIServiceError,
    BulkGenerationResult,
    GeneratedStory,
    RefinementResult,
    RefinementSuggestion,
)
from src.app.shared.logging import IntegrationLogger, get_logger


class GeminiService(AIService):
    """
    Google Gemini-based implementation of AIService.

    Uses the Gemini REST API directly via httpx
    (no SDK dependency required).
    """

    BULK_GENERATION_PROMPT = """You are an expert Agile product owner and business analyst.
Your task is to analyze raw discovery notes and generate multiple well-structured user stories.

Rules:
1. Extract distinct features/requirements from the notes
2. Create 3-7 user stories (depending on complexity)
3. Each story must have:
   - Clear, concise title
   - Description in format: "As a [role], I want to [action] so that [benefit]"
   - 2-4 acceptance criteria in Given-When-Then format
4. Prioritize based on business value and dependencies
5. Ensure each story is independent and testable

Return ONLY a valid JSON object with this exact structure:
{
  "stories": [
    {
      "title": "string",
      "description": "string",
      "acceptance_criteria": ["string", "string", ...],
      "confidence": 0.0-1.0
    }
  ]
}"""

    SYSTEM_PROMPT = """You are an expert Agile product owner and business analyst.
Your task is to refine rough user story drafts into well-structured, professional user stories.

Rules:
1. Titles should be concise, descriptive, and follow standard naming conventions
2. Descriptions must follow the format: "As a [role], I want to [action] so that [benefit]"
3. Acceptance criteria must use Given-When-Then format
4. Each criterion should be testable and unambiguous
5. Provide reasoning for each suggestion

Return ONLY a valid JSON object with this exact structure:
{
  "refined_title": "string",
  "refined_description": "string",
  "refined_criteria": ["string", "string", ...],
  "suggestions": [
    {
      "type": "title|description|criteria",
      "content": "string",
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

    async def refine_story(
        self,
        title: str,
        description: str | None = None,
        acceptance_criteria: list[str] | None = None,
    ) -> RefinementResult:
        """
        Refine a user story using Google Gemini.

        Args:
            title: Raw story title
            description: Raw story description
            acceptance_criteria: Raw acceptance criteria

        Returns:
            RefinementResult with refined content and suggestions

        Raises:
            AIServiceError: If AI service call fails
        """
        user_prompt = self._build_user_prompt(title, description, acceptance_criteria)

        url = f"{self._base_url}/{self._model}:generateContent?key={self._api_key}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [
                            {
                                "role": "user",
                                "parts": [
                                    {"text": self.SYSTEM_PROMPT},
                                    {"text": user_prompt},
                                ],
                            }
                        ],
                        "generationConfig": {
                            "temperature": self._temperature,
                            "maxOutputTokens": self._max_tokens,
                            "responseMimeType": "application/json",
                            "responseSchema": {
                                "type": "object",
                                "properties": {
                                    "refined_title": {"type": "string"},
                                    "refined_description": {"type": "string"},
                                    "refined_criteria": {"type": "array", "items": {"type": "string"}},
                                    "suggestions": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "type": {"type": "string"},
                                                "content": {"type": "string"},
                                                "reasoning": {"type": "string"},
                                                "confidence": {"type": "number"},
                                            },
                                            "required": ["type", "content", "reasoning", "confidence"],
                                        },
                                    },
                                },
                                "required": ["refined_title", "refined_description", "refined_criteria", "suggestions"],
                            },
                        },
                    },
                )

                if response.status_code != 200:
                    raise AIServiceError(f"Gemini API error: {response.status_code} - {response.text}")

                data = response.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"]

                # Log raw response for debugging
                self._log.debug(f"Gemini raw response length: {len(content)} chars")

                return self._parse_response(content)

        except AIServiceError:
            raise
        except Exception as e:
            raise AIServiceError(f"Failed to call Gemini API: {e!s}") from e

    async def is_available(self) -> bool:
        """Check if Gemini service is configured."""
        return bool(self._api_key and self._api_key.strip())

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
                            "maxOutputTokens": 4000,  # More tokens for multiple stories
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
                                                "confidence": {"type": "number"},
                                            },
                                            "required": ["title", "description", "acceptance_criteria", "confidence"],
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

    def _build_user_prompt(
        self,
        title: str,
        description: str | None,
        acceptance_criteria: list[str] | None,
    ) -> str:
        """Build the user prompt from story components."""
        parts = [f"Refine this user story:\n\n**Title:** {title}"]

        if description:
            parts.append(f"**Description:** {description}")
        else:
            parts.append("**Description:** (not provided - please create one)")

        if acceptance_criteria:
            criteria_text = "\n".join(f"- {c}" for c in acceptance_criteria)
            parts.append(f"**Acceptance Criteria:**\n{criteria_text}")
        else:
            parts.append("**Acceptance Criteria:** (not provided - please create some)")

        return "\n\n".join(parts)

    def _parse_response(self, content: str) -> RefinementResult:
        """Parse the AI response JSON into a RefinementResult."""
        try:
            # Clean up content - remove markdown code blocks if present
            json_str = content.strip()
            if "```" in json_str:
                match = re.search(r"```(?:json)?\s*(.*?)\s*```", json_str, re.DOTALL)
                if match:
                    json_str = match.group(1).strip()

            # Try to parse JSON
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                # If JSON is malformed, log it and try to fix common issues
                self._log.warning(f"Malformed JSON from Gemini (length {len(json_str)}): {e!s}")
                self._log.debug(f"Raw content preview: {json_str[:500]}...")

                # Try to extract and fix the JSON
                # Remove any trailing commas before closing braces/brackets
                json_str = re.sub(r",(\s*[}\]])", r"\1", json_str)
                # Try again
                data = json.loads(json_str)

            suggestions = []
            for s in data.get("suggestions", []):
                suggestions.append(
                    RefinementSuggestion(
                        suggestion_type=s.get("type", "title"),
                        content=s.get("content", ""),
                        reasoning=s.get("reasoning", ""),
                        confidence=s.get("confidence", 0.5),
                    )
                )

            return RefinementResult(
                refined_title=data.get("refined_title", ""),
                refined_description=data.get("refined_description"),
                refined_criteria=data.get("refined_criteria", []),
                suggestions=suggestions,
            )

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            self._log.error(f"Failed to parse Gemini response: {e}")
            self._log.error(f"Content that failed: {content[:1000]}")
            raise AIServiceError(f"Invalid Gemini response format: {e!s}") from e

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
                        confidence=story_data.get("confidence", 0.8),
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
