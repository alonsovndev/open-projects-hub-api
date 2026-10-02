import secrets

from src.app.features.auth.application.services.email_links import EmailLinks
from src.app.features.auth.application.use_cases.issue_verification_code import issue_verification_code
from src.app.features.auth.domain.repositories.email_verification_code_repository import EmailVerificationCodeRepository
from src.app.features.user.application.dtos.user_dto import UserCreateRequest, UserResponse
from src.app.features.user.application.mappers.user_dto_mapper import map_create_request_to_entity, to_user_response
from src.app.features.user.domain.exceptions.user_exceptions import UserAlreadyExistsError
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.features.workspaces.domain.exceptions.workspace_exceptions import WorkspaceUserLimitExceededError
from src.app.shared.application.request_context import RequestContext
from src.app.shared.infrastructure.email.email_sender import EmailSender
from src.app.shared.infrastructure.security.password_handler import PasswordHandler
from src.app.shared.logging import get_logger, set_user_id


class CreateUserUseCase:
    """
    Adds a member or viewer to the caller's workspace (up to the workspace user cap) and emails
    them a verification code.

    The account signs in only after the person confirms the address and chooses their own
    password from the emailed link; until then it holds a random password nobody knows.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        verification_code_repository: EmailVerificationCodeRepository,
        email_sender: EmailSender,
        email_links: EmailLinks,
        max_workspace_users: int,
    ):
        self.user_repository = user_repository
        self.verification_code_repository = verification_code_repository
        self.email_sender = email_sender
        self.email_links = email_links
        self.max_workspace_users = max_workspace_users

    async def execute(self, payload: UserCreateRequest, ctx: RequestContext) -> UserResponse:
        log = get_logger(__name__)
        set_user_id(str(ctx.user_id))

        try:
            if await self.user_repository.count_by_workspace(ctx.workspace_id) >= self.max_workspace_users:
                raise WorkspaceUserLimitExceededError(self.max_workspace_users)

            password_hash = await PasswordHandler.hash_password(secrets.token_urlsafe(32))

            new_user_entity = map_create_request_to_entity(payload, password_hash, ctx.workspace_id)

            existing_user = await self.user_repository.find_by_email(new_user_entity.email)

            if existing_user:
                log.warning(
                    "Duplicate user creation attempt",
                    extra={"event_type": "user.create.email_exists", "email": str(new_user_entity.email)},
                )
                raise UserAlreadyExistsError(str(new_user_entity.email))

            created_user = await self.user_repository.save(new_user_entity)

            # Repository returns None if duplicate email exists
            if created_user is None:
                log.warning(
                    "Race condition during user creation",
                    extra={"event_type": "user.create.race_condition", "email": str(new_user_entity.email)},
                )
                raise UserAlreadyExistsError(str(new_user_entity.email))

            await issue_verification_code(
                created_user, self.verification_code_repository, self.email_sender, self.email_links
            )

            response_dto = to_user_response(created_user)

            log.info(
                "User created successfully",
                extra={"event_type": "user.create.success", "user_id": str(created_user.id)},
            )
            return response_dto

        except (ValueError, UserAlreadyExistsError, WorkspaceUserLimitExceededError):
            raise
        except Exception:
            log.exception("Unexpected error in CreateUserUseCase", extra={"event_type": "user.create.unexpected_error"})
            raise
