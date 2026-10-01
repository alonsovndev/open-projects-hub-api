"""Generate multiple stories from raw discovery notes use case."""

from src.app.features.ai_config.application.services.refinement_provider_resolver import RefinementProviderResolver
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.refinement.application.dtos.refinement_dto import GenerateStoriesRequest, GenerateStoriesResponse
from src.app.features.refinement.application.mappers.generated_story_mapper import to_generated_story_response
from src.app.features.refinement.domain.exceptions.refinement_exceptions import RefinementFailedError
from src.app.features.refinement.domain.services.note_sanitizer import NoteSanitizer
from src.app.features.refinement.domain.validators.refinement_validators import RefinementValidators
from src.app.features.refinement.infrastructure.ai.ai_service import AIServiceError
from src.app.features.user.domain.exceptions.user_exceptions import UserNotFoundError
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.application.request_context import RequestContext
from src.app.shared.domain.exceptions.domain_exceptions import NotFoundError, ValidationError
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class GenerateStoriesFromNotesUseCase:
    """Use case for generating multiple refined stories from raw notes using AI."""

    def __init__(
        self,
        provider_resolver: RefinementProviderResolver,
        user_repository: UserRepository,
        project_repository: ProjectRepository,
    ):
        """
        Initialize use case.

        Args:
            provider_resolver: Chooses the AI client for this run and whether it costs a credit
            user_repository: Holds the credit balance that a platform run is charged against
            project_repository: Confirms the target project is in the caller's workspace
        """
        self._provider_resolver = provider_resolver
        self._user_repository = user_repository
        self._project_repository = project_repository

    async def execute(
        self,
        request: GenerateStoriesRequest,
        ctx: RequestContext,
    ) -> GenerateStoriesResponse:
        """
        Execute bulk story generation from raw notes.

        Args:
            request: GenerateStoriesRequest with project_id and raw_notes
            ctx: Caller identity and workspace

        Returns:
            GenerateStoriesResponse with generated stories

        Raises:
            RefinementFailedError: If the AI provider fails; carries the raw notes so the
                Admin can retry without re-entering them
            AICreditsExhaustedError: If a platform run is requested with no credits left
            ApiKeyNotFoundError: If a user provider is requested without a stored key
            NotFoundError: If the project is not in the caller's workspace
        """
        log = get_logger(__name__)
        set_user_id(str(ctx.user_id))
        created_by = str(ctx.user_id)

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

        # Checked before the provider is resolved or called: a foreign project must cost
        # neither a credit nor a provider request.
        project_uuid = EntityId.from_string(request.project_id)
        if not await self._project_repository.exists(project_uuid.value, workspace_id=ctx.workspace_id.value):
            raise NotFoundError("Project", request.project_id)

        user = await self._user_repository.find_by_id(ctx.user_id)
        if user is None:
            raise UserNotFoundError(created_by)

        # Resolves before any provider call, so an exhausted balance or a missing key fails
        # fast without spending a request. Credits are charged only after a successful run.
        resolved = await self._provider_resolver.resolve(user, request.provider)
        ai_service = resolved.service

        try:
            log.info(
                "Starting AI story generation from notes",
                extra={
                    "event_type": "refinement.generate.started",
                    "project_id": request.project_id,
                    "provider": ai_service.provider_name,
                    "consumes_credit": resolved.consumes_credit,
                    "notes_length": len(notes.sanitized),
                    "redaction_count": notes.redaction_count,
                },
            )

            result = await ai_service.generate_stories_from_notes(notes.sanitized)

            log.info(
                "AI service generated stories successfully",
                extra={
                    "event_type": "refinement.generate.ai_completed",
                    "project_id": request.project_id,
                    "story_count": len(result.stories),
                },
            )

            story_responses = [to_generated_story_response(story) for story in result.stories]

            log.info(
                "Stories generated from notes",
                extra={
                    "event_type": "refinement.stories.generated",
                    "entity_id": request.project_id,
                    "story_count": len(story_responses),
                    "notes_length": len(request.raw_notes),
                },
            )

            credits_remaining: int | None = None
            if resolved.consumes_credit:
                # Only now: FR-010-02 requires a failed refinement to leave the balance
                # untouched, so nothing above this point may charge the account.
                #
                # Charged through the repository's conditional UPDATE rather than by
                # mutating `user` and saving it: the snapshot above is tens of seconds old
                # by this point, so a read-modify-write would let two concurrent runs share
                # one credit and would also roll back any password change or forced logout
                # that landed while the provider was working.
                credits_remaining = await self._user_repository.consume_ai_credit(user.id)

                if credits_remaining is None:
                    # The balance was spent by a concurrent run between resolve and here.
                    # The stories are already generated, so the refinement is not failed over
                    # it — the response simply reports an unknown balance and the client
                    # refetches.
                    log.warning(
                        "Credit balance was exhausted before this run could be charged",
                        extra={
                            "event_type": "refinement.credit.charge_missed",
                            "project_id": request.project_id,
                        },
                    )

            return GenerateStoriesResponse(
                stories=story_responses,
                raw_notes=request.raw_notes,
                redaction_count=notes.redaction_count,
                provider=request.provider,
                credits_remaining=credits_remaining,
            )

        except AIServiceError as e:
            # Logged without the exception message: provider errors can echo request detail.
            log.error(
                "AI provider failed during story generation",
                extra={
                    "event_type": "refinement.generate.provider_failed",
                    "project_id": request.project_id,
                    "provider": ai_service.provider_name,
                    "failure_class": e.failure_class.value,
                },
            )
            raise RefinementFailedError(
                failure_class=e.failure_class,
                raw_notes=request.raw_notes,
                provider=ai_service.provider_name,
            ) from e

        except Exception:
            log.exception(
                "Failed to generate stories from notes",
                extra={"event_type": "refinement.generate.failed", "project_id": request.project_id},
            )
            raise
