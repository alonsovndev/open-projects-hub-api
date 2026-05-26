from datetime import datetime

from src.app.features.user.domain.value_objects.email import Email
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.entities.base_entity import BaseEntity
from src.app.shared.domain.value_objects.entity_id import EntityId


class UserEntity(BaseEntity):
    def __init__(
        self,
        id: EntityId,
        email: Email,
        display_name: str,
        password_hash: str,
        role: UserRole = UserRole.VIEWER,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.email = email
        self.display_name = display_name
        self.password_hash = password_hash
        self.role = role
        super().__init__(id, created_at, updated_at)

    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN
