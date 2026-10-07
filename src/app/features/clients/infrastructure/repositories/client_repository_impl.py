"""Client repository implementation."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.clients.domain.entities.client_entity import ClientEntity
from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.features.clients.infrastructure.mappers.client_mapper import ClientMapper
from src.app.features.clients.infrastructure.models.client_model import ClientModel
from src.app.shared.logging import get_logger


class ClientRepositoryImpl(ClientRepository):
    """PostgreSQL implementation of ClientRepository."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._log = get_logger(__name__)

    async def save(self, client: ClientEntity) -> ClientEntity:
        """Save a new client entity."""
        model = ClientMapper.to_model(client)
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return ClientMapper.to_entity(model)

    async def find_by_id(self, client_id: UUID, *, workspace_id: UUID) -> ClientEntity | None:
        """Find a client of the workspace by ID."""
        stmt = select(ClientModel).where(ClientModel.id == client_id, ClientModel.workspace_id == workspace_id)
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return ClientMapper.to_entity(model)

    async def find_all(self, *, workspace_id: UUID, skip: int = 0, limit: int = 100) -> list[ClientEntity]:
        """Find the workspace's clients with pagination."""
        stmt = (
            select(ClientModel)
            .where(ClientModel.workspace_id == workspace_id)
            .order_by(ClientModel.name.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        models = result.scalars().all()

        return [ClientMapper.to_entity(model) for model in models]

    async def count(self, *, workspace_id: UUID) -> int:
        """Count the workspace's clients."""
        stmt = select(func.count()).select_from(ClientModel).where(ClientModel.workspace_id == workspace_id)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def update(self, client: ClientEntity) -> ClientEntity:
        """Update an existing client entity."""
        if client.workspace_id is None:
            raise ValueError(f"Client has no workspace: {client.id.value}")
        stmt = select(ClientModel).where(
            ClientModel.id == client.id.value, ClientModel.workspace_id == client.workspace_id.value
        )
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"Client not found: {client.id.value}")

        # Update model fields
        model.name = client.name
        model.email = client.email.value if client.email else None
        model.phone = client.phone.value if client.phone else None
        model.company = client.company
        model.address = client.address
        model.notes = client.notes
        model.updated_at = client.updated_at

        await self.db.commit()
        await self.db.refresh(model)

        return ClientMapper.to_entity(model)

    async def delete(self, client_id: UUID, *, workspace_id: UUID) -> bool:
        """Delete a client of the workspace."""
        stmt = select(ClientModel).where(ClientModel.id == client_id, ClientModel.workspace_id == workspace_id)
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return False

        await self.db.delete(model)
        await self.db.commit()
        return True

    async def find_by_email(self, email: str, *, workspace_id: UUID) -> ClientEntity | None:
        """Find a client of the workspace by email address."""
        stmt = select(ClientModel).where(ClientModel.email == email, ClientModel.workspace_id == workspace_id)
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return ClientMapper.to_entity(model)
