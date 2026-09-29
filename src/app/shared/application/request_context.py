"""Who is calling, and which tenant their request is confined to."""

from dataclasses import dataclass

from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.entity_id import EntityId


@dataclass(frozen=True)
class RequestContext:
    user_id: EntityId
    workspace_id: EntityId
    role: UserRole

    @property
    def can_edit(self) -> bool:
        return self.role in (UserRole.ADMIN, UserRole.MEMBER)
