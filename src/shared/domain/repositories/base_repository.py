from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional

from src.shared.domain.value_objects.entity_id import EntityId

T = TypeVar('T')
ID = TypeVar('ID')


class BaseRepository(Generic[T, ID], ABC):
    """
    A generic base repository interface for managing entities.
    """

    @abstractmethod
    async def save(self, entity: T) -> T:
        """
        Save an entity to the repository.

        Args:
            entity (T): The entity to save.

        Returns:
            T: The saved entity.
        """
        pass

    @abstractmethod
    async def find_by_id(self, entity_id: EntityId) -> Optional[T]:
        """
        Find an entity by its unique identifier.

        Args:
            entity_id (ID): The unique identifier of the entity.

        Returns:
            Optional[T]: The entity if found, None otherwise.
        """
        pass

    @abstractmethod
    async def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """
        Find all entities with optional pagination.

        Args:
            limit (Optional[int], optional): Maximum number of entities to return. Defaults to None.
            offset (Optional[int], optional): Number of entities to skip. Defaults to None.

        Returns:
            List[T]: A list of entities.
        """
        pass

    @abstractmethod
    async def exists(self, entity_id: ID) -> bool:
        """
        Check if an entity exists by its unique identifier.

        Args:
            entity_id (ID): The unique identifier of the entity.

        Returns:
            bool: True if the entity exists, False otherwise.
        """
        pass

    @abstractmethod
    async def update(self, entity: T) -> Optional[T]:
        """
        Update an existing entity in the repository.

        Args:
            entity (T): The entity to update.

        Returns:
            Optional[T]: The updated entity if successful, None if the entity was not found.
        """
        pass

    @abstractmethod
    async def delete(self, entity_id: ID) -> bool:
        """
        Delete an entity by its unique identifier.

        Args:
            entity_id (ID): The unique identifier of the entity to delete.

        Returns:
            bool: True if the entity was deleted, False if not found.
        """
        pass
