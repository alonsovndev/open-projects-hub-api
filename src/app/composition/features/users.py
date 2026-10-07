"""
Users feature dependency composition.

All dependency wiring for user management and profile use cases.

Dependencies:
- Infrastructure: Database session
- Repositories:
  - UserRepository (shared, also used by auth and dashboard)

Use Cases:
- Create User: Admin-only user creation
- Get User by ID: Retrieve user details
- Get User Profile: Retrieve current user's profile
- Update User Profile: Modify profile information
- Update User Status: Admin activates or deactivates a teammate
- Delete User: Admin permanently deletes a teammate, handing their work to the Admin
- Change Password: Update user password with validation

Usage:
    from src.app.composition import get_get_user_profile_use_case

    @router.get("/profile")
    async def get_profile(
        use_case: GetUserProfileUseCase = Depends(get_get_user_profile_use_case),
    ):
        return await use_case.execute(...)
"""

from fastapi import Depends

from src.app.composition.features.auth import get_verification_code_repository
from src.app.composition.infrastructure import get_email_links, get_email_sender
from src.app.composition.repositories import get_user_repository
from src.app.composition.workspace_limits import get_workspace_limits
from src.app.features.auth.application.services.email_links import EmailLinks
from src.app.features.auth.domain.repositories.email_verification_code_repository import EmailVerificationCodeRepository
from src.app.features.user.application.use_cases.change_password import ChangePasswordUseCase
from src.app.features.user.application.use_cases.create_user import CreateUserUseCase
from src.app.features.user.application.use_cases.delete_user import DeleteUserUseCase
from src.app.features.user.application.use_cases.get_user_by_id import GetUserByIdUseCase
from src.app.features.user.application.use_cases.get_user_profile import GetUserProfileUseCase
from src.app.features.user.application.use_cases.list_workspace_users import ListWorkspaceUsersUseCase
from src.app.features.user.application.use_cases.update_user_profile import UpdateUserProfileUseCase
from src.app.features.user.application.use_cases.update_user_status import UpdateUserStatusUseCase
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.infrastructure.email.email_sender import EmailSender


# Use case factories
async def get_create_user_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
    verification_code_repository: EmailVerificationCodeRepository = Depends(get_verification_code_repository),
    email_sender: EmailSender = Depends(get_email_sender),
    email_links: EmailLinks = Depends(get_email_links),
) -> CreateUserUseCase:
    """CreateUserUseCase factory."""
    return CreateUserUseCase(
        user_repository, verification_code_repository, email_sender, email_links, get_workspace_limits().max_users
    )


async def get_get_user_by_id_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> GetUserByIdUseCase:
    """GetUserByIdUseCase factory."""
    return GetUserByIdUseCase(user_repository)


async def get_list_workspace_users_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> ListWorkspaceUsersUseCase:
    """ListWorkspaceUsersUseCase factory."""
    return ListWorkspaceUsersUseCase(user_repository)


async def get_get_user_profile_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> GetUserProfileUseCase:
    """GetUserProfileUseCase factory."""
    return GetUserProfileUseCase(user_repository)


async def get_update_user_profile_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> UpdateUserProfileUseCase:
    """UpdateUserProfileUseCase factory."""
    return UpdateUserProfileUseCase(user_repository)


async def get_change_password_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> ChangePasswordUseCase:
    """ChangePasswordUseCase factory."""
    return ChangePasswordUseCase(user_repository)


async def get_update_user_status_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> UpdateUserStatusUseCase:
    """UpdateUserStatusUseCase factory."""
    return UpdateUserStatusUseCase(user_repository)


async def get_delete_user_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> DeleteUserUseCase:
    """DeleteUserUseCase factory."""
    return DeleteUserUseCase(user_repository)
