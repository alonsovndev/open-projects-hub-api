from src.app.features.application.dtos.user_dto import UserCreateRequest
from src.app.features.application.use_cases.create_user import CreateUserUseCase
from src.app.features.application.use_cases.get_user_by_id import GetUserByIdUseCase
from src.app.features.domain.repositories.user_repository import UserRepository


class UserService:

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.create_user_use_case = CreateUserUseCase(user_repository)

    async def get_user_by_id(self, user_id: str):

        use_case = GetUserByIdUseCase(self.user_repository)

        return await use_case.execute(user_id)

    async def create_user(self, payload: UserCreateRequest):
        return await self.create_user_use_case.execute(payload)