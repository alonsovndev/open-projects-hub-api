"""Generate multiple stories from raw discovery notes use case."""

from src.app.features.refinement.application.dtos.refinement_dto import (
    GeneratedStoryResponse,
    GenerateStoriesRequest,
    GenerateStoriesResponse,
)
from src.app.features.refinement.application.mappers.story_draft_mapper import to_generated_story_response
from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.exceptions.refinement_exceptions import RefinementFailedError
from src.app.features.refinement.domain.repositories.story_draft_repository import StoryDraftRepository
from src.app.features.refinement.domain.services.note_sanitizer import NoteSanitizer
from src.app.features.refinement.domain.validators.refinement_validators import RefinementValidators
from src.app.features.refinement.infrastructure.ai.ai_service import AIService, AIServiceError
from src.app.shared.domain.exceptions.domain_exceptions import ValidationError
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class GenerateStoriesFromNotesUseCase:
    """Use case for generating multiple story drafts from raw notes using AI."""

    def __init__(
        self,
        repository: StoryDraftRepository,
        ai_service: AIService,
    ):
        """
        Initialize use case.

        Args:
            repository: Story draft repository
            ai_service: AI service for story generation
        """
        self._repository = repository
        self._ai_service = ai_service

    async def execute(
        self,
        request: GenerateStoriesRequest,
        created_by: str,
    ) -> GenerateStoriesResponse:
        """
        Execute bulk story generation from raw notes.

        Args:
            request: GenerateStoriesRequest with project_id and raw_notes
            created_by: User UUID string who created the drafts

        Returns:
            GenerateStoriesResponse with generated stories

        Raises:
            RefinementFailedError: If the AI provider fails; carries the raw notes so the
                Admin can retry without re-entering them
        """
        log = get_logger(__name__)
        set_user_id(created_by)

        notes = NoteSanitizer.sanitize(request.raw_notes)

        # Sanitization can empty out a note that was entirely markup or injection payload.
        # Sending that to the provider would bill a call on nothing, so it is rejected
        # here; the caller still holds the raw input it submitted.
        if len(notes.sanitized) < RefinementValidators.MIN_NOTES_LENGTH:
            log.warning(
                "Refinement input was left too short after sanitization",
                extra={
                    "event_type": "refinement.generate.sanitized_empty",
                    "project_id": request.project_id,
                    "redaction_count": notes.redaction_count,
                },
            )
            raise ValidationError(
                "After removing markup and instruction-like content, too little text remained "
                f"to refine (minimum {RefinementValidators.MIN_NOTES_LENGTH} characters). "
                "Rewrite the notes as plain prose or a bullet list."
            )

        try:
            log.info(
                "Starting AI story generation from notes",
                extra={
                    "event_type": "refinement.generate.started",
                    "project_id": request.project_id,
                    "provider": self._ai_service.provider_name,
                    "notes_length": len(notes.sanitized),
                    "redaction_count": notes.redaction_count,
                },
            )

            result = await self._ai_service.generate_stories_from_notes(notes.sanitized)

            log.info(
                "AI service generated stories successfully",
                extra={
                    "event_type": "refinement.generate.ai_completed",
                    "project_id": request.project_id,
                    "story_count": len(result.stories),
                },
            )

            project_uuid = EntityId.from_string(request.project_id)
            creator_uuid = EntityId.from_string(created_by)

            story_responses: list[GeneratedStoryResponse] = []

            for generated_story in result.stories:
                draft = StoryDraftEntity.create(
                    title=generated_story.title,
                    description=generated_story.description,
                    acceptance_criteria=generated_story.acceptance_criteria,
                    project_id=project_uuid,
                    created_by=creator_uuid,
                )

                saved_draft = await self._repository.save(draft)

                story_responses.append(
                    to_generated_story_response(
                        draft_id=str(saved_draft.id.value),
                        generated_story=generated_story,
                    )
                )

            log.info(
                "Stories generated from notes",
                extra={
                    "event_type": "refinement.stories.generated",
                    "entity_id": request.project_id,
                    "story_count": len(story_responses),
                    "notes_length": len(request.raw_notes),
                },
            )

            return GenerateStoriesResponse(
                stories=story_responses,
                raw_notes=request.raw_notes,
                redaction_count=notes.redaction_count,
            )

        except AIServiceError as e:
            # Logged without the exception message: provider errors can echo request detail.
            log.error(
                "AI provider failed during story generation",
                extra={
                    "event_type": "refinement.generate.provider_failed",
                    "project_id": request.project_id,
                    "provider": self._ai_service.provider_name,
                    "failure_class": e.failure_class.value,
                },
            )
            raise RefinementFailedError(
                failure_class=e.failure_class,
                raw_notes=request.raw_notes,
                provider=self._ai_service.provider_name,
            ) from e

        except Exception:
            log.exception(
                "Failed to generate stories from notes",
                extra={"event_type": "refinement.generate.failed", "project_id": request.project_id},
            )
            raise
