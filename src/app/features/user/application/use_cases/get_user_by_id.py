from src.app.features.user.application.dtos.user_dto_mapper import UserResponse, map_entity_to_dto_user
from src.app.features.user.application.exceptions.user_exception import UserDoesNotExistException
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import BusinessLogger, get_logger


class GetUserByIdUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: str) -> UserResponse:
        log = BusinessLogger(get_logger(__name__), user_id=user_id)

        try:
            user_obj_id = EntityId.from_string(user_id)

            existing_user = await self.user_repository.find_by_id(user_obj_id)

            if not existing_user:
                log.failure("user.not_found", entity_id=user_id)
                raise UserDoesNotExistException(user_id)

            return map_entity_to_dto_user(existing_user)

        except ValueError:
            raise
        except UserDoesNotExistException:
            raise
        except Exception:
            raise
