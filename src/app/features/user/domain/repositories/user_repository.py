"""User repository interface."""

from abc import ABC, abstractmethod

from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId


class UserRepository(ABC):
    """Repository interface for User aggregate."""

    @abstractmethod
    async def find_by_id(self, entity_id: EntityId) -> UserEntity | None:
        """
        Find a user by their unique identifier.

        Args:
            entity_id: The unique identifier of the user.

        Returns:
            Optional[UserEntity]: The user entity if found, None otherwise.
        """

    @abstractmethod
    async def find_by_email(self, email: Email) -> UserEntity | None:
        """
        Find a user by their email address.

        Args:
            email: The email address to search for.

        Returns:
            Optional[UserEntity]: The user entity if found, None otherwise.
        """

    @abstractmethod
    async def find_by_name(self, record: str) -> UserEntity | None:
        """
        Find a user by their name.

        Args:
            record: The name of the user to search for.

        Returns:
            Optional[UserEntity]: The user entity if found, None otherwise.
        """

    @abstractmethod
    async def save(self, user: UserEntity) -> UserEntity | None:
        """
        Save a user entity (create or update).

        Args:
            user: UserEntity to save.

        Returns:
            Optional[UserEntity]: The saved user if successful, None if duplicate email exists.
        """

    @abstractmethod
    async def find_all(
        self, workspace_id: EntityId, limit: int | None = None, offset: int | None = None
    ) -> list[UserEntity]:
        """
        Users of one workspace, newest first, with optional pagination.

        Args:
            workspace_id: Tenant whose users are listed
            limit: Maximum number of results (default None = all)
            offset: Number of results to skip (default None = 0)
        """

    @abstractmethod
    async def exists(self, entity_id: EntityId) -> bool:
        """
        Check if a user exists by their unique identifier.

        Args:
            entity_id: The unique identifier of the user.

        Returns:
            bool: True if the user exists, False otherwise.
        """

    @abstractmethod
    async def update(self, user: UserEntity) -> UserEntity | None:
        """
        Update an existing user entity.

        Args:
            user: The user entity to update.

        Returns:
            Optional[UserEntity]: The updated user if successful, None if not found.
        """

    @abstractmethod
    async def delete(self, entity_id: EntityId) -> bool:
        """
        Delete a user by their unique identifier.

        Args:
            entity_id: The unique identifier of the user to delete.

        Returns:
            bool: True if the user was deleted, False if not found.
        """

    @abstractmethod
    async def delete_handing_over(self, entity_id: EntityId, successor_id: EntityId) -> bool:
        """
        Delete a user after moving the projects and stories they created, and the stories
        assigned to them, to the successor. All or nothing.

        Returns:
            bool: True if the user was deleted, False if not found.
        """

    @abstractmethod
    async def consume_ai_credit(self, entity_id: EntityId) -> int | None:
        """
        Atomically spend one AI credit and return the new balance.

        A read-modify-write through `find_by_id` + `update` cannot be used here. A
        refinement holds its user snapshot across a 10-45 second provider call, so two
        concurrent runs would both read the same balance and both write it minus one —
        charging one credit for two refinements. A full-row `update` would also rewrite
        `password_hash` and `token_version` from that stale snapshot, undoing a password
        change or a forced logout that happened while the provider was working.

        Implementations must therefore perform a single conditional UPDATE.

        Args:
            entity_id: The user to charge.

        Returns:
            The remaining balance after the charge, or None if the user does not exist or
            had no credits left to spend.
        """
