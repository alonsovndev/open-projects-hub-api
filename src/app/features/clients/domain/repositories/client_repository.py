"""Client repository interface."""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.app.features.clients.domain.entities.client_entity import ClientEntity


class ClientRepository(ABC):
    """Repository interface for client persistence."""
    
    @abstractmethod
    async def save(self, client: ClientEntity) -> ClientEntity:
        """Save a client entity."""
        pass
    
    @abstractmethod
    async def find_by_id(self, client_id: UUID) -> Optional[ClientEntity]:
        """Find a client by ID."""
        pass
    
    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[ClientEntity]:
        """Find all clients with pagination."""
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """Count total number of clients."""
        pass
    
    @abstractmethod
    async def update(self, client: ClientEntity) -> ClientEntity:
        """Update a client entity."""
        pass
    
    @abstractmethod
    async def delete(self, client_id: UUID) -> bool:
        """Delete a client by ID. Returns True if deleted, False if not found."""
        pass
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[ClientEntity]:
        """Find a client by email address."""
        pass
