from datetime import datetime
from typing import Optional

from src.app.features.domain.value_objects.email import Email
from src.app.features.domain.value_objects.user_role import UserRole
from src.app.shared.domain.entities.base_entity import BaseEntity
from src.app.shared.domain.value_objects.entity_id import EntityId


class UserEntity(BaseEntity):

    def __init__(
        self,
        id: EntityId,
        email: Email,
        first_name: str,
        last_name: str,
        password_hash: str,
        role: UserRole = UserRole.USER,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.password_hash = password_hash
        self.role = role
        super().__init__(id, created_at, updated_at)

    @property
    def display_name(self) -> str:
        """Full name for display purposes."""
        return f"{self.first_name} {self.last_name}"

    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN
