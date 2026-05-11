"""
RefreshTokenUseCase - Refresh access token using refresh token.
"""
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.features.user.domain.value_objects.email import Email
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler
from src.app.shared.utils.log_util import log
import jwt


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Response model for token refresh."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    access_token: str
    refresh_token: str


class RefreshTokenUseCase:
    """
    Use case for refreshing access tokens using refresh tokens.
    
    Implements token rotation: each refresh generates a new access token
    AND a new refresh token, invalidating the old refresh token.
    """

    def __init__(self, user_repository: UserRepository, jwt_handler: JWTHandler):
        self.user_repository = user_repository
        self.jwt_handler = jwt_handler

    async def execute(self, payload: RefreshTokenRequest) -> RefreshTokenResponse:
        """
        Refresh access token using refresh token.
        
        Args:
            payload: RefreshTokenRequest with refresh token
            
        Returns:
            RefreshTokenResponse with new access and refresh tokens
            
        Raises:
            jwt.ExpiredSignatureError: If refresh token has expired
            jwt.InvalidTokenError: If refresh token is invalid
            ValueError: If user not found
        """
        try:
            # Decode and validate refresh token
            refresh_payload = self.jwt_handler.decode_refresh_token(payload.refresh_token)
            
            user_id = refresh_payload.get("sub")
            email = refresh_payload.get("email")
            
            # Verify user still exists
            user_entity = await self.user_repository.find_by_email(Email(email))
            
            if not user_entity:
                log.warning(f"Refresh token used for non-existent user: {email}")
                raise ValueError("User not found")
            
            # Verify user_id matches
            if str(user_entity.id) != user_id:
                log.warning(f"User ID mismatch in refresh token for email: {email}")
                raise jwt.InvalidTokenError("Invalid user credentials in token")
            
            # Generate new access token
            new_access_token = self.jwt_handler.create_access_token(
                user_id=str(user_entity.id),
                email=str(user_entity.email),
                role=user_entity.role.value,
            )
            
            # Generate new refresh token (token rotation)
            new_refresh_token = self.jwt_handler.create_refresh_token(
                user_id=str(user_entity.id),
                email=str(user_entity.email),
                role=user_entity.role.value,
            )
            
            log.info(f"Tokens refreshed successfully for user: {user_id}")
            
            return RefreshTokenResponse(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
            )

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            raise
        except Exception as e:
            log.error(f"Unexpected error in RefreshTokenUseCase: {str(e)}")
            raise
