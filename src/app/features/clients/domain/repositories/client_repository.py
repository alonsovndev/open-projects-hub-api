"""Client repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.app.features.clients.domain.entities.client_entity import ClientEntity


class ClientRepository(ABC):
    """Repository interface for client persistence."""

    @abstractmethod
    async def save(self, client: ClientEntity) -> ClientEntity:
        """Save a client entity."""

    @abstractmethod
    async def find_by_id(self, client_id: UUID) -> ClientEntity | None:
        """Find a client by ID."""

    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> list[ClientEntity]:
        """Find all clients with pagination."""

    @abstractmethod
    async def count(self) -> int:
        """Count total number of clients."""

    @abstractmethod
    async def update(self, client: ClientEntity) -> ClientEntity:
        """Update a client entity."""

    @abstractmethod
    async def delete(self, client_id: UUID) -> bool:
        """Delete a client by ID. Returns True if deleted, False if not found."""

    @abstractmethod
    async def find_by_email(self, email: str) -> ClientEntity | None:
        """Find a client by email address."""
