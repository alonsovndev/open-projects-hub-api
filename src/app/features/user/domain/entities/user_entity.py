from datetime import datetime

from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.entities.base_entity import BaseEntity
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId


class UserEntity(BaseEntity):
    def __init__(
        self,
        id: EntityId,
        email: Email,
        display_name: str,
        password_hash: str,
        role: UserRole = UserRole.VIEWER,
        token_version: int = 0,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self._email = email
        self._display_name = display_name
        self._password_hash = password_hash
        self._role = role
        self._token_version = token_version
        super().__init__(id, created_at, updated_at)

    @property
    def email(self) -> Email:
        return self._email

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @property
    def role(self) -> UserRole:
        return self._role

    @property
    def token_version(self) -> int:
        return self._token_version

    @classmethod
    def create(
        cls,
        email: str,
        display_name: str,
        password_hash: str,
        role: UserRole | None = None,
    ) -> "UserEntity":
        return cls(
            id=EntityId.generate(),
            email=Email(email),
            display_name=display_name,
            password_hash=password_hash,
            role=role or UserRole.default(),
        )

    def update_details(
        self,
        email: str | None = None,
        display_name: str | None = None,
        password_hash: str | None = None,
        role: UserRole | None = None,
    ) -> None:
        if email is not None:
            self._email = Email(email)
        if display_name is not None:
            self._display_name = display_name
        if password_hash is not None:
            self._password_hash = password_hash
        if role is not None:
            self._role = role
        self.mark_as_updated()

    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self._role == UserRole.ADMIN

    def revoke_sessions(self) -> None:
        """
        Invalidate every refresh token issued before this call (forced logout
        across all devices). Refresh tokens embed the token_version they were
        issued under; bumping it makes older tokens fail validation.
        """
        self._token_version += 1
        self.mark_as_updated()
