"""OpenAI-compatible chat-completions implementation of AIService (OpenAI and DeepSeek)."""

import json
import re

import httpx

from src.app.features.refinement.domain.services.story_generation_prompt import BULK_GENERATION_PROMPT
from src.app.features.refinement.domain.value_objects.refinement_failure_class import RefinementFailureClass
from src.app.features.refinement.infrastructure.ai.ai_service import (
    AIService,
    AIServiceError,
    BulkGenerationResult,
    GeneratedStory,
)
from src.app.shared.infrastructure.retry import retry_on_exception
from src.app.shared.logging import get_logger


class OpenAICompatibleService(AIService):
    """
    Story generation over the OpenAI `/chat/completions` contract.

    One class serves both OpenAI and DeepSeek because DeepSeek implements the same
    request and response shape; only the base URL, model, and provider label differ.
    A second near-identical class would be duplication, not clarity.

    Uses raw httpx rather than a vendor SDK, matching `GeminiService` — it keeps the
    dependency surface flat and the failure modes uniform across providers.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        provider_label: str,
        temperature: float = 0.3,
        max_tokens: int = 2500,
    ):
        """
        Args:
            api_key: The user's provider API key.
            model: Model identifier to request.
            base_url: Provider API root, e.g. `https://api.openai.com/v1`.
            provider_label: Short provider identifier, safe to log.
            temperature: Sampling temperature (lower is more deterministic).
            max_tokens: Maximum response tokens.
        """
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._provider_label = provider_label
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._log = get_logger(__name__)

    @property
    def provider_name(self) -> str:
        """Provider identifier used in logs and failure responses."""
        return self._provider_label

    async def is_available(self) -> bool:
        """Check the service holds a key. A live check costs a validation attempt."""
        return bool(self._api_key and self._api_key.strip())

    @retry_on_exception(max_tries=3)
    async def generate_stories_from_notes(self, raw_notes: str) -> BulkGenerationResult:
        """
        Generate user stories from raw discovery notes.

        Args:
            raw_notes: Raw discovery notes, already sanitized by the caller.

        Returns:
            BulkGenerationResult with generated stories.

        Raises:
            AIServiceError: If the provider call or response parsing fails.
        """
        user_prompt = (
            f"Analyze these discovery notes and generate user stories.\n\n<user_input>\n{raw_notes}\n</user_input>"
        )

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    # The key travels in a header, never the query string: httpx puts the
                    # request URL into its exception messages, which would land the key in
                    # logs and Sentry.
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self._api_key}",
                    },
                    json={
                        "model": self._model,
                        "messages": [
                            {"role": "system", "content": BULK_GENERATION_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": self._temperature,
                        "max_tokens": self._max_tokens,
                        "response_format": {"type": "json_object"},
                    },
                )

                if response.status_code != 200:
                    self._log.error(
                        "Provider API returned a non-success status",
                        extra={
                            "event_type": "refinement.provider.error",
                            "provider": self.provider_name,
                            "status_code": response.status_code,
                        },
                    )
                    raise AIServiceError(
                        f"{self.provider_name} API error: HTTP {response.status_code}",
                        failure_class=RefinementFailureClass.PROVIDER_ERROR,
                    )

                data = response.json()
                content = data["choices"][0]["message"]["content"]

                return self._parse_bulk_generation(content, raw_notes)

        except AIServiceError:
            raise
        except httpx.TimeoutException as e:
            raise AIServiceError(
                f"{self.provider_name} API call timed out",
                failure_class=RefinementFailureClass.TIMEOUT,
            ) from e
        except Exception as e:
            # Only the exception type is reported: httpx messages can embed request detail,
            # and this request carries the user's API key in its headers.
            raise AIServiceError(
                f"Failed to call {self.provider_name} API for bulk generation: {type(e).__name__}",
                failure_class=RefinementFailureClass.PROVIDER_ERROR,
            ) from e

    def _parse_bulk_generation(self, content: str, raw_notes: str) -> BulkGenerationResult:
        """Parse the chat-completions payload into generated stories."""
        try:
            json_str = content.strip()
            if "```" in json_str:
                match = re.search(r"```(?:json)?\s*(.*?)\s*```", json_str, re.DOTALL)
                if match:
                    json_str = match.group(1).strip()

            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                self._log.warning("Malformed JSON from bulk generation: %s", e)
                json_str = re.sub(r",(\s*[}\]])", r"\1", json_str)
                data = json.loads(json_str)

            stories = [
                GeneratedStory(
                    title=story_data.get("title", "Untitled Story"),
                    description=story_data.get("description", ""),
                    acceptance_criteria=story_data.get("acceptance_criteria", []),
                )
                for story_data in data.get("stories", [])
            ]

            return BulkGenerationResult(stories=stories, raw_notes=raw_notes)

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            self._log.exception(
                "Failed to parse bulk generation response",
                extra={"event_type": "refinement.provider.invalid_response", "provider": self.provider_name},
            )
            raise AIServiceError(
                f"Invalid bulk generation response format: {e!s}",
                failure_class=RefinementFailureClass.INVALID_RESPONSE,
            ) from e
