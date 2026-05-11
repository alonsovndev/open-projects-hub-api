"""
RegisterUserUseCase - Public registration with auto-login.

Following API spec requirements:
- Public endpoint (no auth required)
- Default role: viewer
- Returns JWT token (auto-login behavior)
- Returns AdminLoginResponse (same format as login)
"""
from src.app.features.user.application.dtos.auth_dto import AdminLoginResponse
from src.app.features.user.application.dtos.user_dto import UserCreateRequest
from src.app.features.user.application.dtos.user_dto_mapper import map_create_request_to_entity
from src.app.features.user.application.exceptions.user_exception import UserAlreadyExistsException
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler
from src.app.shared.infrastructure.security.password_handler import PasswordHandler
from src.app.shared.utils.log_util import log


class RegisterUserUseCase:
    """
    Use case for user registration with auto-login.
    
    Creates a new user with default viewer role and returns JWT token
    for immediate authentication (auto-login behavior).
    """

    def __init__(self, user_repository: UserRepository, jwt_handler: JWTHandler):
        self.user_repository = user_repository
        self.jwt_handler = jwt_handler

    async def execute(self, payload: UserCreateRequest) -> AdminLoginResponse:
        """
        Register new user and return JWT token (auto-login).
        
        Args:
            payload: User registration data (email, password, displayName)
            
        Returns:
            AdminLoginResponse with JWT token and user details
            
        Raises:
            UserAlreadyExistsException: If email already exists
            ValueError: If validation fails
        """
        try:
            # Hash password
            password_hash = await PasswordHandler.hash_password(payload.password)

            # Create entity (default role = viewer)
            new_user_entity = map_create_request_to_entity(payload, password_hash)

            # Check for existing user
            existing_user = await self.user_repository.find_by_email(new_user_entity.email)

            if existing_user:
                log.warning(f"Registration attempt with existing email: {new_user_entity.email}")
                raise UserAlreadyExistsException(str(new_user_entity.email))

            # Save user
            created_user = await self.user_repository.save(new_user_entity)
            
            # Handle race condition
            if created_user is None:
                log.warning(f"Race condition: User with email {new_user_entity.email} was created by another request")
                raise UserAlreadyExistsException(str(new_user_entity.email))

            # Generate JWT tokens (auto-login)
            token = self.jwt_handler.create_access_token(
                user_id=str(created_user.id.value),
                email=str(created_user.email.value),
                role=created_user.role.value
            )
            
            refresh_token = self.jwt_handler.create_refresh_token(
                user_id=str(created_user.id.value),
                email=str(created_user.email.value),
                role=created_user.role.value
            )

            # Return login response format
            response = AdminLoginResponse.from_user_entity(created_user, token, refresh_token)

            log.info(f"User registered successfully: {created_user.id}")
            return response

        except (ValueError, UserAlreadyExistsException):
            raise
        except Exception as e:
            log.error(f"Unexpected error in RegisterUserUseCase: {str(e)}")
            raise
