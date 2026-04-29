from src.app.features.application.dtos.auth_dto import AdminLoginResponse, LoginRequest
from src.app.features.application.use_cases.login_user import LoginUserUseCase
from src.app.features.domain.repositories.user_repository import UserRepository
from src.shared.infrastructure.security.jwt_handler import JWTHandler


class AuthService:
    """
    Service layer for authentication operations.
    Orchestrates use cases and provides high-level auth methods.
    """

    def __init__(self, user_repository: UserRepository, jwt_handler: JWTHandler):
        self.user_repository = user_repository
        self.jwt_handler = jwt_handler
        self.login_use_case = LoginUserUseCase(user_repository, jwt_handler)

    async def login(self, payload: LoginRequest) -> AdminLoginResponse:
        """
        Authenticates user and returns login response.

        Args:
            payload: LoginRequest with email and password

        Returns:
            AdminLoginResponse with token and user details

        Raises:
            InvalidCredentialsError: If credentials are invalid
        """
        return await self.login_use_case.execute(payload)
