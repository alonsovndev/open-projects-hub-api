"""
RegisterUserUseCase - Public registration with auto-login.

Following API spec requirements:
- Public endpoint (no auth required)
- Role: admin, assigned server-side and never taken from the request
- Returns JWT token (auto-login behavior)
- Returns AdminLoginResponse (same format as login)
"""

from src.app.features.auth.application.dtos.auth_dto import AdminLoginResponse, RegisterRequest
from src.app.features.auth.application.mappers.auth_mapper import to_admin_login_response
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.exceptions.user_exceptions import UserAlreadyExistsError
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler
from src.app.shared.infrastructure.security.password_handler import PasswordHandler
from src.app.shared.logging import get_logger, set_user_id


class RegisterUserUseCase:
    """
    Use case for user registration with auto-login.

    Creates a new admin account and returns a JWT token for immediate authentication
    (auto-login behavior). The role is fixed here rather than derived from the payload:
    registration is anonymous, so any role the caller could influence would be a
    privilege-escalation path.
    """

    def __init__(self, user_repository: UserRepository, jwt_handler: JWTHandler):
        self.user_repository = user_repository
        self.jwt_handler = jwt_handler

    async def execute(self, payload: RegisterRequest) -> AdminLoginResponse:
        """
        Register new user and return JWT token (auto-login).

        Args:
            payload: User registration data (email, password, displayName)

        Returns:
            AdminLoginResponse with JWT token and user details

        Raises:
            UserAlreadyExistsError: If email already exists
            ValueError: If validation fails
        """
        log = get_logger(__name__)
        set_user_id(str(payload.email))

        try:
            password_hash = await PasswordHandler.hash_password(payload.password)

            new_user_entity = UserEntity.create(
                email=str(payload.email).lower().strip(),
                display_name=payload.display_name.strip(),
                password_hash=password_hash,
                role=UserRole.ADMIN,
            )

            # Enforce email uniqueness constraint at application layer
            existing_user = await self.user_repository.find_by_email(new_user_entity.email)

            if existing_user:
                log.warning(
                    "Registration attempt with existing email",
                    extra={"event_type": "auth.register.email_exists", "email": str(new_user_entity.email)},
                )
                raise UserAlreadyExistsError(str(new_user_entity.email))

            created_user = await self.user_repository.save(new_user_entity)

            # Handle race condition where another request created the user between check and save
            if created_user is None:
                log.warning(
                    "Race condition during registration",
                    extra={"event_type": "auth.register.race_condition", "email": str(new_user_entity.email)},
                )
                raise UserAlreadyExistsError(str(new_user_entity.email))

            token = self.jwt_handler.create_access_token(
                user_id=str(created_user.id.value), email=str(created_user.email.value), role=created_user.role.value
            )

            refresh_token = self.jwt_handler.create_refresh_token(
                user_id=str(created_user.id.value),
                email=str(created_user.email.value),
                role=created_user.role.value,
                token_version=created_user.token_version,
            )
            session_expires_at = self.jwt_handler.get_token_expiry(refresh_token)

            response = to_admin_login_response(created_user, token, refresh_token, session_expires_at)

            log.info(
                "User registered successfully",
                extra={"event_type": "auth.register.success", "user_id": str(created_user.id.value)},
            )
            return response

        except (ValueError, UserAlreadyExistsError):
            raise
        except Exception:
            log.exception(
                "Unexpected error in RegisterUserUseCase", extra={"event_type": "auth.register.unexpected_error"}
            )
            raise
