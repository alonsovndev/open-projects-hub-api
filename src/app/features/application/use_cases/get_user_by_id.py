from uuid import UUID

from src.app.features.application.dtos.user_dto_mapper import UserResponse, map_entity_to_dto_user
from src.app.features.application.exceptions.user_exception import UserDoesNotExistException
from src.app.features.domain.repositories.user_repository import UserRepository
from src.shared.domain.value_objects.entity_id import EntityId
from src.shared.utils.log_util import log


class GetUserByIdUseCase:

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: str) -> UserResponse:
        try:
            user_obj_id = EntityId.from_string(user_id)

            existing_user = await self.user_repository.find_by_id(user_obj_id)

            if not existing_user:
                log.warning(f"User not found with ID: {user_id}")
                raise UserDoesNotExistException(user_id)

            response_dto = map_entity_to_dto_user(existing_user)

            return response_dto

        except ValueError as e:
            raise
        except UserDoesNotExistException as e:
            raise
        except Exception as e:
            raise
