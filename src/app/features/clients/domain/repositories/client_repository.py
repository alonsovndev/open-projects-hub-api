"""Client repository interface.

Every read and delete is confined to one workspace. A client of another workspace behaves
exactly like one that does not exist, so callers answer 404 and never reveal it.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from src.app.features.clients.domain.entities.client_entity import ClientEntity


class ClientRepository(ABC):
    """Repository interface for client persistence."""

    @abstractmethod
    async def save(self, client: ClientEntity) -> ClientEntity:
        """Save a client entity (the entity carries its workspace)."""

    @abstractmethod
    async def find_by_id(self, client_id: UUID, *, workspace_id: UUID) -> ClientEntity | None:
        """Find a client of the workspace by ID."""

    @abstractmethod
    async def find_all(self, *, workspace_id: UUID, skip: int = 0, limit: int = 100) -> list[ClientEntity]:
        """Find the workspace's clients with pagination."""

    @abstractmethod
    async def count(self, *, workspace_id: UUID) -> int:
        """Count the workspace's clients."""

    @abstractmethod
    async def update(self, client: ClientEntity) -> ClientEntity:
        """Update a client entity within its own workspace."""

    @abstractmethod
    async def delete(self, client_id: UUID, *, workspace_id: UUID) -> bool:
        """Delete a client of the workspace. Returns True if deleted, False if not found."""

    @abstractmethod
    async def find_by_email(self, email: str, *, workspace_id: UUID) -> ClientEntity | None:
        """Find a client of the workspace by email address."""
