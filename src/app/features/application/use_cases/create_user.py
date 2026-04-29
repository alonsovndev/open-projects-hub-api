from src.app.features.application.dtos.user_dto import UserCreateRequest, UserResponse
from src.app.features.application.dtos.user_dto_mapper import map_create_request_to_entity, map_entity_to_dto_user
from src.app.features.application.exceptions.user_exception import UserAlreadyExistsException
from src.app.features.domain.repositories.user_repository import UserRepository
from src.app.shared.infrastructure.security.password_handler import PasswordHandler
from src.app.shared.utils.log_util import log


class CreateUserUseCase:

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, payload: UserCreateRequest) -> UserResponse:
        try:
            password_hash = PasswordHandler.hash_password(payload.password)

            new_user_entity = map_create_request_to_entity(payload, password_hash)

            existing_user = await self.user_repository.find_by_email(new_user_entity.email)

            if existing_user:
                log.warning(f"Duplicate user creation attempt with email: {new_user_entity.email}")
                raise UserAlreadyExistsException(str(new_user_entity.email))

            created_user = await self.user_repository.save(new_user_entity)

            response_dto = map_entity_to_dto_user(created_user)

            log.info(f"User created successfully: {created_user.id}")
            return response_dto

        except (ValueError, UserAlreadyExistsException):
            raise
        except Exception as e:
            log.error(f"Unexpected error in CreateUserUseCase: {str(e)}")
            raise