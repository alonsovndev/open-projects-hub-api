"""Mapper between Client entity and Client model."""

from src.app.features.clients.domain.entities.client_entity import ClientEntity
from src.app.features.clients.infrastructure.models.client_model import ClientModel
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.domain.value_objects.phone_number import PhoneNumber


class ClientMapper:
    """Maps between ClientEntity and ClientModel."""

    @staticmethod
    def to_entity(model: ClientModel) -> ClientEntity:
        """Convert ClientModel to ClientEntity."""
        return ClientEntity(
            id=EntityId.from_string(str(model.id)),
            name=model.name,
            email=Email(model.email) if model.email else None,
            phone=PhoneNumber(model.phone) if model.phone else None,
            company=model.company,
            address=model.address,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
            workspace_id=EntityId.from_string(str(model.workspace_id)) if model.workspace_id else None,
        )

    @staticmethod
    def to_model(entity: ClientEntity) -> ClientModel:
        """Convert ClientEntity to ClientModel."""
        return ClientModel(
            id=entity.id.value,
            name=entity.name,
            email=entity.email.value if entity.email else None,
            phone=entity.phone.value if entity.phone else None,
            company=entity.company,
            address=entity.address,
            notes=entity.notes,
            workspace_id=entity.workspace_id.value if entity.workspace_id else None,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
