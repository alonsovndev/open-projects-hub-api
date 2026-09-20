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
    async def find_all(self, limit: int | None = None, offset: int | None = None) -> list[UserEntity]:
        """
        Find all users with optional pagination.

        Args:
            limit: Maximum number of results (default None = all).
            offset: Number of results to skip (default None = 0).

        Returns:
            List[UserEntity]: A list of user entities.
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
    async def exists_any(self) -> bool:
        """
        Check whether any user account exists at all.

        Used to decide whether public registration is still open: the first account
        bootstraps the instance's Admin, and every account after that is created by an
        existing Admin.

        Returns:
            bool: True if at least one user exists, False if the instance has none.
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
