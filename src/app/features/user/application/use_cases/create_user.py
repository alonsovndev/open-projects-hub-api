from src.app.features.user.application.dtos.user_dto import UserCreateRequest, UserResponse
from src.app.features.user.application.dtos.user_dto_mapper import map_create_request_to_entity, map_entity_to_dto_user
from src.app.features.user.application.exceptions.user_exception import UserAlreadyExistsException
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.infrastructure.security.password_handler import PasswordHandler
from src.app.shared.logging import BusinessLogger, get_logger


class CreateUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, payload: UserCreateRequest, created_by: str) -> UserResponse:
        log = BusinessLogger(get_logger(__name__), user_id=created_by)

        try:
            password_hash = await PasswordHandler.hash_password(payload.password)

            new_user_entity = map_create_request_to_entity(payload, password_hash)

            existing_user = await self.user_repository.find_by_email(new_user_entity.email)

            if existing_user:
                log.warning(
                    "Duplicate user creation attempt",
                    event_type="user.create.email_exists",
                    email=str(new_user_entity.email),
                )
                raise UserAlreadyExistsException(str(new_user_entity.email))

            created_user = await self.user_repository.save(new_user_entity)

            # Repository returns None if duplicate email exists
            if created_user is None:
                log.warning(
                    "Race condition during user creation",
                    event_type="user.create.race_condition",
                    email=str(new_user_entity.email),
                )
                raise UserAlreadyExistsException(str(new_user_entity.email))

            response_dto = map_entity_to_dto_user(created_user)

            log.info("User created successfully", event_type="user.create.success", user_id=str(created_user.id))
            return response_dto

        except (ValueError, UserAlreadyExistsException):
            raise
        except Exception as e:
            log.error("Unexpected error in CreateUserUseCase", error=e, error_type="user.create.unexpected_error")
            raise
