from src.app.features.user.application.dtos.auth_dto import AdminLoginResponse, LoginRequest
from src.app.features.user.domain.exceptions.auth_exceptions import InvalidCredentialsError
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.features.user.domain.value_objects.email import Email
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler
from src.app.shared.infrastructure.security.password_handler import PasswordHandler
from src.app.shared.utils.log_util import log


class LoginUserUseCase:
    """
    Use case for authenticating users and issuing JWT tokens.
    """

    def __init__(self, user_repository: UserRepository, jwt_handler: JWTHandler):
        self.user_repository = user_repository
        self.jwt_handler = jwt_handler

    async def execute(self, payload: LoginRequest) -> AdminLoginResponse:
        """
        Authenticates user and returns login response with JWT token.

        Args:
            payload: LoginRequest with email and password

        Returns:
            AdminLoginResponse with token and user details

        Raises:
            InvalidCredentialsError: If credentials are invalid
        """
        try:
            user_entity = await self.user_repository.find_by_email(
                Email(str(payload.email).lower().strip())
            )

            if not user_entity:
                log.warning(f"Login attempt with non-existent email: {payload.email}")
                raise InvalidCredentialsError()

            password_valid = await PasswordHandler.verify_password(
                payload.password,
                user_entity.password_hash,
            )
            
            if not password_valid:
                log.warning(f"Failed login attempt for user: {user_entity.id}")
                raise InvalidCredentialsError()

            token = self.jwt_handler.create_access_token(
                user_id=str(user_entity.id),
                email=str(user_entity.email),
                role=user_entity.role.value,
            )
            
            refresh_token = self.jwt_handler.create_refresh_token(
                user_id=str(user_entity.id),
                email=str(user_entity.email),
                role=user_entity.role.value,
            )

            response = AdminLoginResponse.from_user_entity(user_entity, token, refresh_token)

            log.info(f"User logged in successfully: {user_entity.id}")
            return response

        except InvalidCredentialsError:
            raise
        except Exception as e:
            log.error(f"Unexpected error in LoginUserUseCase: {str(e)}")
            raise
