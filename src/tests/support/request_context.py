"""Builds the caller context that tenant-scoped use cases receive from the route layer."""

from uuid import UUID

from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.application.request_context import RequestContext
from src.app.shared.domain.value_objects.entity_id import EntityId


TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440001"
TEST_WORKSPACE_ID = "550e8400-e29b-41d4-a716-4466554400ff"


def make_request_context(
    user_id: str = TEST_USER_ID, workspace_id: str = TEST_WORKSPACE_ID, role: UserRole = UserRole.ADMIN
) -> RequestContext:
    return RequestContext(
        user_id=EntityId(UUID(user_id)),
        workspace_id=EntityId(UUID(workspace_id)),
        role=role,
    )


TEST_WORKSPACE_UUID = UUID(TEST_WORKSPACE_ID)
