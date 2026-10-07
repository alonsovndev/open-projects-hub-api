"""Workspace repository interface."""

from abc import ABC, abstractmethod

from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.workspaces.domain.entities.workspace_entity import WorkspaceEntity
from src.app.shared.domain.value_objects.entity_id import EntityId


class WorkspaceRepository(ABC):
    @abstractmethod
    async def create_with_admin(
        self, workspace: WorkspaceEntity, admin: UserEntity, replacing: UserEntity | None = None
    ) -> UserEntity | None:
        """
        Persist a new workspace together with its first Admin in one transaction.

        `replacing` is an unverified account holding the same email; it is removed in the
        same transaction (with its workspace, when it was that workspace's pending Admin).
        An unverified account never proved the address, so it must not block the owner.

        Returns None when the admin's email is already taken; nothing is persisted then,
        so a lost race never leaves an orphan workspace behind.
        """

    @abstractmethod
    async def find_by_id(self, workspace_id: EntityId) -> WorkspaceEntity | None:
        """Workspace by id, or None."""

    @abstractmethod
    async def reserve_ai_credits(self, workspace_id: EntityId, amount: int, ceiling: int) -> int:
        """
        Atomically reserve up to `amount` free credits from the workspace's lifetime `ceiling`.

        Returns the number actually reserved (0 once the ceiling is reached). The reservation
        is permanent: it is not returned if the user is later removed. It joins the current
        transaction and is persisted by the caller's next commit (the user update).
        """

    @abstractmethod
    async def update(self, workspace: WorkspaceEntity) -> WorkspaceEntity:
        """Persist the workspace's current name and return the stored workspace."""
